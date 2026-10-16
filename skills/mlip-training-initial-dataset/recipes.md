# Recipes for the static families and MD sampling

Materials-agnostic snippets, one per family.
Each is a starting point to adapt, with the parameters that usually matter named.
Every structure is written as geometry only; energies and forces come from DFT later.

## Foundation-model calculator and relaxation

```python
from ase.filters import FrechetCellFilter
from ase.optimize import FIRE

def mace_calc(dtype='float64'):
    from mace.calculators import mace_mp     # model names as of 2026, check the current release
    return mace_mp(model='medium-mpa-0', default_dtype=dtype)  # or a MACECalculator on a named model file

def nep89_calc(model_file='nep89.txt'):
    from calorine.calculators import CPUNEP   # calorine.calculators.GPUNEP for GPU
    return CPUNEP(model_file)

def relax(atoms, calc, fmax=0.01, steps=400, cell=True):
    atoms.calc = calc
    target = FrechetCellFilter(atoms) if cell else atoms
    FIRE(target, logfile=None).run(fmax=fmax, steps=steps)
    atoms.calc = None            # detach before writing
    return atoms
```

Use a tight fmax (0.001 to 0.01) for the few relaxed prototypes that are kept, a loose one (0.05) for screening sets such as enumerations.
Check the space group before and after; a prototype that relaxes into another is a duplicate.

```python
from calorine.tools import get_spacegroup
print(get_spacegroup(atoms, symprec=1e-3))
```

## Prototypes

```python
from ase.build import bulk
protos = {'fcc': bulk('X', 'fcc', a=4.0), 'bcc': bulk('X', 'bcc', a=3.2),
          'hcp': bulk('X', 'hcp', a=2.8, c=4.5), 'diamond': bulk('X', 'diamond', a=5.4)}
```

Materials Project query for known polymorphs (needs an API key in `MP_API_KEY`):

```python
from mp_api.client import MPRester
with MPRester() as mpr:
    docs = mpr.materials.summary.search(formula='AB2', fields=['material_id', 'structure', 'symmetry', 'energy_above_hull'])
from pymatgen.io.ase import AseAtomsAdaptor
atoms_list = [AseAtomsAdaptor.get_atoms(d.structure) for d in docs]
```

Chemical substitution from an analogous compound: replace the species, scale the cell by the ratio of ionic or covalent radii, then relax.

```python
from ase.io import read, write
atoms = read('analogue.cif')
atoms.symbols = [sub.get(s, s) for s in atoms.get_chemical_symbols()]
atoms.set_cell(atoms.cell * scale, scale_atoms=True)
```

## Strained and sheared cells

```python
import numpy as np
rng = np.random.default_rng(0)

def scaled(atoms, s):                        # lattice scale s about 0.94 to 1.10 (volume 0.83 to 1.33)
    a = atoms.copy(); a.set_cell(a.cell * s, scale_atoms=True); return a

def strained(atoms, lim=0.08):               # independent axis stretches
    s = rng.uniform(-lim, lim, 3)
    a = atoms.copy(); a.set_cell(a.cell[:] * (1 + s), scale_atoms=True); return a

def deformed(atoms, lim=0.05):               # general deformation incl. shear
    M = np.eye(3) + rng.uniform(-lim, lim, (3, 3))
    a = atoms.copy(); a.set_cell(M @ a.cell[:], scale_atoms=True); return a
```

Find the limits by scanning one prototype and reading off where the energy per atom climbs steeply (a few tenths of an eV above the minimum is plenty).

## Rattled cells

```python
def rattled(atoms, stdev=0.05, seed=0):
    a = atoms.copy(); a.rattle(stdev=stdev, seed=seed); return a
```

Use 0.03 to 0.10 Å on relaxed cells, several seeds, often combined with a small volume scale.
Monte Carlo rattling (`hiphive.structure_generation.generate_mc_rattled_structures`) avoids too-close pairs at larger amplitudes.

## Enumeration for alloys and mixed occupancy

```python
from icet.tools import enumerate_structures
for atoms in enumerate_structures(parent, sizes=[2, 3, 4], chemical_symbols=['A', 'B']):
    relax(atoms, calc, fmax=0.05, steps=100)
```

Sizes 2 to 4 per parent lattice give tens of structures; cap the count by random subsampling rather than larger sizes.
For sublattice disorder pass a list of allowed symbols per site.
Random special-quasirandom-like cells at a few compositions complement the enumeration at larger sizes.

## Surfaces

```python
from ase.build import fcc100, fcc110, fcc111, bcc100, bcc110, bcc111, surface
slab = fcc111('X', size=(3, 4, 6), a=4.0, vacuum=10.0, orthogonal=True)   # vacuum is per side, so 20 Å in total
slab.pbc = True; slab.info.pop('adsorbate_info', None)
general = surface(bulk_atoms, indices=(1, 1, 0), layers=6, vacuum=10.0)
```

Vacuum of 15 to 20 Å in total for DFT (ASE `vacuum=` is per side), slab thickness set per orientation so the middle layers stay bulk-like, and a small in-plane cell (3x3 is usually enough).
Keep terminations charge neutral and stoichiometric unless the user asks for polar ones.

## Point defects

```python
atoms = relaxed.repeat(n)                    # aim for about 100 atoms
for sym in set(atoms.get_chemical_symbols()):
    i = atoms.symbols.indices()[sym][0]
    vac = atoms.copy(); del vac[i]
    vac.info['family'] = 'vacancy'
    write(f'{tag}_vacancy-{sym}_natoms{len(vac)}.xyz', relax(vac, calc, cell=False))
```

Interstitials: place the atom at the largest void (a grid of candidate points, keep the one with the largest nearest-neighbour distance), then relax positions.
Antisites: swap two symbols of different species.
Keep defect cells charge neutral or note the compensation.

## Nanoparticles

```python
from ase.cluster import wulff_construction, Octahedron
cluster = wulff_construction('X', surfaces=[(1, 0, 0), (1, 1, 1)], energies=[1.0, 0.9], size=80, structure='fcc')
cluster.center(vacuum=10.0); cluster.pbc = True
```

For compounds, cut a sphere from a bulk supercell, detect molecules before shifting anything, and check that the particle is one connected piece with the intended shape before keeping it.

## MD sampling

Ramp with ASE, re-creating the integrator per stage; GPUMD with NEP89 does the same faster for large sets.

```python
from ase.md.langevin import Langevin
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution, Stationary
from ase import units

def ramp(atoms, calc, t_start, t_stop, ps, dt_fs=2.0, dump_ps=0.5, n_stages=10, seed=0):
    atoms.calc = calc
    MaxwellBoltzmannDistribution(atoms, temperature_K=t_start, rng=np.random.default_rng(seed)); Stationary(atoms)
    steps_per_stage = int(ps * 1000 / dt_fs / n_stages); dump_every = int(dump_ps * 1000 / dt_fs)
    frames = []
    for k in range(n_stages):
        T = t_start + (t_stop - t_start) * (k + 1) / n_stages
        dyn = Langevin(atoms, dt_fs * units.fs, temperature_K=T, friction=0.01 / units.fs)
        for _ in range(steps_per_stage // dump_every):
            dyn.run(dump_every)
            f = atoms.copy(); f.info.update(T_target=T, T=atoms.get_temperature()); frames.append(f)
    return frames
```

Use an NPT integrator (`ase.md.nose_hoover_chain.IsotropicMTKNPT` or GPUMD `npt_mttk`) for bulk ramps so the volume follows temperature, and NVT at fixed strained cells.
Melt-quench: expand the cell a few percent, hold well above the melting point for half the run, then quench linearly.
Start molecular and hybrid systems near 100 K.

Frame selection, evenly in time with a per-run offset so runs cover different parts of the ramp:

```python
def pick(frames, n, skip=5, phase=0.5):
    frames = frames[skip:]
    idx = ((np.arange(n) + phase) / n * (len(frames) - 1)).round().astype(int)
    return [frames[i] for i in idx]
phase = (0.2, 0.5, 0.8)[sum(map(ord, run_name)) % 3]
```

Each pick passes the gate (contacts above floors, molecules intact) before it is written; take the nearest passing frame otherwise.

## Pushed-pair contacts

One pair in a thermal host frame moved to a short distance, so the DFT single point isolates that repulsion.

```python
from ase.neighborlist import neighbor_list

def min_margin(atoms, floors, skip):             # smallest (distance - floor) over every pair except skip
    i, j, d = neighbor_list('ijd', atoms, max(floors.values()) + 0.5)
    sym = np.array(atoms.get_chemical_symbols())
    keep = ~(((i == skip[0]) & (j == skip[1])) | ((i == skip[1]) & (j == skip[0])))
    return min(dd - floors[tuple(sorted((a, b)))] for a, b, dd in zip(sym[i[keep]], sym[j[keep]], d[keep]))

def push(host, i, j, d, floors, n_dir=60, seed=0):
    rng = np.random.default_rng(seed)
    vec = host.get_distance(i, j, mic=True, vector=True)
    dirs = np.vstack([vec / np.linalg.norm(vec), rng.normal(size=(n_dir, 3))])
    dirs /= np.linalg.norm(dirs, axis=1)[:, None]
    best = None
    for u in dirs:
        a = host.copy(); a.positions[j] += d * u - vec; a.wrap()
        margin = min_margin(a, floors, skip=(i, j))
        if best is None or margin > best[0]:
            best = (margin, a)
    return best[1]
```

Pushing along the pair axis alone can land the atom on a bridging neighbour, hence the direction search.
Move a whole molecule rigidly when the pushed atom belongs to one.
Take host frames from several runs and temperatures, and distances from about 0.7 to 0.9 of the equilibrium pair distance; check that the foundation-model force on the pushed pair stays under the project's force cap before DFT.

## File naming

`<prefix>_<prototype>_<family>_<change>_T<K>_natoms<N>.xyz`, for example `AB_fcc_strained_iso0.94_natoms32.xyz` or `AB_bcc_2x2x3_MD_ramp100-1200_T850_f031_natoms96.xyz`.
Family tokens, the single list the skill, the recipes and the verifier share: `prototype`, `strained`, `rattled`, `enumerated`, `surface`, `vacancy`, `interstitial`, `antisite`, `nano`, `MD`, `contact`.
Contact files name their pair and distance as `_contact_<A><B>-<d>_`, for example `AB_fcc_contact_AB-1.8_natoms96.xyz`, so the verifier can exempt that pair.
Store `family`, `description` and `T_target` in `atoms.info` so the manifest can be rebuilt from the files.
