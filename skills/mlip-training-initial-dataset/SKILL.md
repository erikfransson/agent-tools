---
name: mlip-training-initial-dataset
description: Use when building the first training set for a machine-learned interatomic potential (NEP, MACE, any MLIP) and no project model exists yet, so sampling runs on foundation models. Triggers on "initial dataset", "initial training set", "gen-1 structures", "bootstrap training data".
---

# MLIP initial dataset

The goal is a first training set of roughly 100 to 300 structures whose local environments are so diverse that the gen-1 model survives its first MD campaign.
No project model exists yet, so a **foundation model** does the relaxations and the MD sampling.
The hard part is coverage: every phase, temperature, strain and defect the user cares about should be represented by a few structures, and no family should dominate.
Failure modes of the trained model are patched later with the sibling skill `mlip-training-active-learning-for-stability`, so an even spread matters more here than depth on any one family.

This skill ends when the structures sit on disk as single extxyz files, listed in a manifest, and an independent reviewer has passed them.
It ends at the DFT-ready set.
The numbers in it are rough guides.

## Words used here

- **Prototype**: a crystal structure, molecule or cluster that seeds a family (fcc, bcc, a polytype, a known compound after substitution).
- **Family**: one kind of structure, named by one of the tokens listed under File naming in [`recipes.md`](recipes.md) (prototype, strained, rattled, enumerated, surface, vacancy, interstitial, antisite, nano, MD, contact). Every output file carries its family in its name and info.
- **Protocol**: one MD recipe (ramp, hold, melt-quench, strained-cell run) with its temperature window.
- **Gate**: a hard check a structure must pass before it is kept (contacts above floors, intact molecules, atom count in budget, sane density).
- **Manifest**: the tsv listing every structure with name, family, natoms, temperature and a one-line note.

## 1. Interview

Before building anything, ask the user one round of questions, numbered, each with a recommended default, so "defaults" is a valid answer.
Look up facts yourself first (existing structure files in the repo, the composition, what databases return for it); ask only for decisions.
Ask a second round only when an answer opens a new branch (an alloy brings composition and enumeration sizes, a molecular system brings timestep and start temperature).

Cover at least:

- **Phases and prototypes**: which bulk phases (fcc, bcc, hcp, known polymorphs, polytypes), liquid or melt, amorphous, and whether analogous compounds should be substituted in. Default: every known polymorph plus the common prototypes of the lattice type, plus a melt.
- **Conditions**: temperature window, pressure or volume range, whether the model will be used far above the melting point. Default: from about 100 K to well above the use temperature, lattice scale about 0.94 to 1.10 of equilibrium (volume 0.83 to 1.33).
- **Size budget**: target number of structures and atoms per cell. Default: 100 to 300 structures, most cells 1 to 300 atoms, hard cap about 400, with several supercell shapes per prototype.
- **Static families**: a few relaxed prototypes (default yes, a handful, they carry little information), volume and shear scans (default yes), rattled copies (default yes, useful for phonons), enumeration for alloys or mixed occupancy (default yes when the system has mixed sites).
- **Extended families**: surfaces, vacancies, interstitials, antisites, grain boundaries, nanoparticles, stacking faults. Default: surfaces and single vacancies only when the model will be used for them; ask rather than assume.
- **Pushed-pair contacts**: a few cells with one short pair to teach repulsion. Default yes, 5 to 15, from several host frames.
- **Calculator**: a universal MLIP, as of 2026 the MACE-MP family by default and NEP89 for simple ionic or metallic systems where speed matters more. Prefer the one that keeps a test prototype intact and whose training functional is closest to the project DFT, and name it in the manifest notes.
- **Where to write**: the structures directory and file naming, following the layout the repo already uses.

The interview is done when every family has a yes, no or count, and the budget and output location are fixed.

## 2. Collect prototypes

- Start from structure files already in the project.
- Prefer Materials Project (an API key is assumed; ask if the query fails), and add OQMD, AFLOW or COD when it comes back thin; ICSD and CSD need a licence the user may have.
- Search the literature for cif files of the compound and of chemically similar compounds, then substitute species and rescale the lattice.
- For elements and simple lattices use `ase.build.bulk` and hand-built cells.
- Deduplicate before and after relaxation with a structure matcher (pymatgen `StructureMatcher` or the neighbour-distance fingerprint of the example verifier); a prototype that relaxes into another is dropped, and one that changes its connectivity is kept under a changed label only if its density is still sane.
- Relax with the foundation model (cell and positions, tight fmax for the few prototypes that are kept as static structures, loose for screening sets).

The step is done when every phase named in the interview has at least one prototype on disk, with its source noted.

## 3. Build the static families

[`recipes.md`](recipes.md) holds materials-agnostic snippets for each family.
Rough counts for a 200-structure set, scaled to the user's budget and answers:

| family             | how                                                           | rough count |
|:-------------------|:--------------------------------------------------------------|:------------|
| relaxed prototype  | tight relax of each kept prototype                            | 5 to 15     |
| strained           | lattice scale 0.94 to 1.10, uniaxial, shear up to about 6 %   | 10 to 30    |
| rattled            | 0.03 to 0.10 Å random displacements on relaxed cells          | 5 to 15     |
| enumerated         | icet enumeration over sizes 2 to 4 per parent lattice         | 10 to 40    |
| surface            | 2 or 3 low-index facets, 15 to 20 Å vacuum for DFT            | 5 to 15     |
| vacancy, interstitial, antisite | one vacancy per species, an interstitial, an antisite | 5 to 15 |
| nano               | one or two particles cut from each phase, with vacuum         | 0 to 10     |
| contact            | one pushed pair in a thermal host frame                       | 5 to 15     |

Choose strain limits by scanning one prototype for where the energy climbs steeply, then stay inside that.
Vary the supercell shape as well as the size between members of a family, since cell shape changes which environments appear.
Keep cells for DFT as small as the family allows: a vacancy in about 100 atoms, a surface in the thinnest slab that still has a bulk-like middle.

The step is done when every static family the user asked for has its files written, each name stating prototype, family and what was changed.

## 4. MD snapshots

MD snapshots supply the thermal environments and usually half the set.

- **Calculator**: the foundation model chosen in the interview, float32 for MD. Test it on one prototype first: a model that tears molecules apart or melts a crystal far below its known melting point is the wrong model for that family.
- **Protocols**: heating ramps from low to above the use temperature as the main protocol, short holds at a few temperatures, a melt-quench for liquid and amorphous frames, and runs at fixed strained cells. A frame is called molten only after its coordination says so.
- **Cells**: every prototype, in several supercell shapes, all within the atom cap.
- **Timestep**: 0.5 to 1 fs with hydrogen, 1 to 2 fs when any light element (up to about Cl) is present, up to 5 fs when every species is heavy.
- **Dumps**: every 0.25 to 1 ps; consecutive frames are nearly redundant, so dense dumps only waste disk.
- **Selection**: per run, a quota by family; discard the first few ps, then spread the picks evenly in time with an offset fixed per run, so different runs cover different parts of the ramp. Each pick passes the gate before it is kept.
- **Contacts**: build the pushed pairs from several selected thermal frames, not one, so the repulsion data spans environments.

The step is done when every protocol in the plan has run on every prototype, the picks are on disk with family, temperature and frame in their names, and the coverage table (family × temperature × natoms) shows no empty cell the user asked for.

## 5. Assemble and review

- Write every structure as one extxyz file into the structures directory with a descriptive name: prefix, prototype, family, what was changed, temperature for MD frames, natoms.
- Write the manifest and a short dataset report: counts and atom range per family, a temperature histogram, the atom-count median and the share at or below 300 atoms.
- [`verify_dataset_example.py`](verify_dataset_example.py) is a starting point for the project's own gate: composition, contacts against per-pair floors, atom count, vacuum detection, near-duplicates, and the summary tables.

Then an **independent review** by a fresh subagent or fresh code, so the builder's assumptions are not reused, checks that every structure is what its name claims and that the set as a whole matches the interview:

- composition, charge neutrality and intact molecules in every file;
- every pair distance above its floor, including in contact files apart from the named pair, with floors for H-H and anion-anion pairs measured from clean thermal frames rather than taken from covalent radii;
- labels re-measured from the structure (phase, coordination, connectivity, molten or crystalline, particle shape and connectedness), since a label is a claim;
- density within a sane band for cells that changed on relaxation;
- no near-duplicates, and file names matching the stored info;
- the distribution against the interview: every requested family present, MD snapshots at most about half of the set and spread over protocols and temperatures, no static family above about a fifth, the temperature window and the strain range covered.

Fix or drop what fails, rerun the review, and repeat until it comes back clean or every remaining gap is named with its reason.

The skill is done when the review passes and the structures, manifest and report sit in the project's directory ready for the DFT pipeline.

## Delegation

The steps above split into independent small tasks: a literature or database search, relaxing a batch of prototypes, one MD batch, the review of step 5.
Hand those to subagents with lower capability and effort than the main session (a smaller model at medium effort does most of them), run them in parallel, and keep the plan and the final judgement in the main session.
