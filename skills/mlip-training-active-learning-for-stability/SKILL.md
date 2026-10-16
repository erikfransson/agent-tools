---
name: mlip-training-active-learning-for-stability
description: Use when a machine-learned interatomic potential (NEP, MACE, any MLIP) breaks in MD and the next training generation should patch it, or when planning stability-driven structure generation for a new model generation. Triggers on "patch failure modes", "stability runs", "model breaks in MD", "pick failure structures for DFT", "active learning for stability".
---

# MLIP active learning for stability

The goal is a next-generation model that no longer fails where the current one does.
The route: provoke every **failure mode** of the current models in MD, find the **onset** of each, and send DFT the frames right at that onset, so training learns the true energy there and the path to collapse closes.
Extra equilibrium data rarely does this, and a few dozen well-chosen onset frames often do.

This skill describes the process.
The numbers in it are rough guides, and the right cell sizes, run lengths and counts depend on the system, the DFT cost and the compute at hand.

## Words used here

- **Failure mode**: one distinct way the structure goes wrong (a bond class breaking, a close contact, desorption, framework collapse, volume runaway), per molecule or motif and per model.
- **Onset**: the first frame where a failure starts. Note whether it persists or recovers, since a brief excursion is a weaker signal.
- **Pre-onset frame**: a frame shortly before or at the onset, with the structure still physical. These are the frames worth DFT.
- **Ledger**: the table of failure modes found so far, one row per event (run, model, motif, mode, T, time, failure or excursion).

## 1. Design the hunt

- **Every prototype**: start from all prototype structures in the project whose stability should be fixed.
- **Small cells suitable for DFT**: DFT is much cheaper for small cells, so smaller is better, and the selected frames then go straight to DFT. Some failure modes only appear in larger cells (collective events), and those need a few larger cells, with small windows cut around the event site afterwards.
- **Supercell diversity**: vary the supercell between seeds (for example 1x1x1, 1x2x1, 2x2x1, 3x2x1, 2x5x3), since cell shape and size change which failures appear.
- **Every model**: run every model variant at hand (tiers, seeds, hyperparameter variants). Each fails in its own places.
- **Many seeds**: many independent velocity seeds per model and prototype, weighted toward combinations that already fail in stability tests. A failure that is rare per molecule shows up once the seed count is high enough.
- **Heating ramps** as the main protocol: from a low temperature to well above the temperature the model will be used at. Each run puts its onset at one random temperature.
- **Holds** as the complement: a short undumped ramp to a temperature near a known onset, then a dumped hold there. Holds give many independent onsets near the temperature where a failure starts.
- **Dense dumps**: every 10 to 20 fs, so the last physical frame before an onset is on disk. Also dump one reference frame right after the initial minimisation.
- Start hybrid or molecular systems near 100 K, since a hot start with random velocities can tear the cell apart and fake a failure.

Fit the run length to the cluster's time and utilisation limits and to the disk space for full dumps, using a short benchmark of speed and dump size per frame.
How the runs are grouped into batches follows from storage and queue limits.

The step is done when the runs cover every prototype and model, with seeds weighted toward the known failures, and the first runs are confirmed stepping.

## 2. Find the onsets

Scan every frame of every run against the reference frame.
Look for, at least:

- **Close contacts**: the shortest distance per element pair below a floor (H-H, heavy-atom pairs, cation-cation, metal-metal), and fusion of neighbouring molecules.
- **Bond graph changes** among heavy atoms (cleavage, new bonds, group transfer), and completed H hops versus shared protons.
- **Detached atoms** and fragments, desorption of molecules from a surface.
- **Framework damage**: coordination loss, broken corner sharing, metal-metal pairs, ion loss.
- **Runaway**: volume or cell shape, temperature, energy.

[`onset_scan_example.py`](onset_scan_example.py) shows the core of such a scan: shortest distance per element pair, a volume band and a heavy-atom bond graph, reporting the first unphysical frame and the frames before it.
It is a starting point and inspiration for a project's own scanner, with example floors for a lead-iodide perovskite.
Calibrate the floors by plotting the per-pair curves of a few runs: too tight catches normal thermal motion, too loose hides a mode.

Scan strided first, then rescan densely around each candidate to place the onset exactly.
Check a few flagged events by eye.

The step is done when every run is scanned and every event sits in the ledger with its mode, model, T and time.

## 3. Keep the ledger and close the gaps

Summarise the ledger as a table of motif × mode × model, with the T range and the number of independent runs per mode.
Read it for **gaps**: modes seen in only one run, models never run on a motif, modes known from other tests (large-cell stability runs, earlier generations) but missing here.
Point further runs at the gaps: more seeds on thin modes, holds near their onset T, other models or cell sizes.

The hunt is done when every mode in the ledger has events from several independent runs, or is named as a gap with the reason it stays open.

## 4. Select the frames

- **Per mode**: roughly 5 to 15 frames, drawn from several independent runs, so the same mode is seen along slightly different paths. Within one event, take frames just before, at and just after the onset.
- **Per prototype**: aim for roughly 15 to 100 frames in total. A project with many molecules or motifs ends up with more overall.
- Spend the budget where the models fail most. A motif that never fails needs few or no failure frames.
- Pick for diversity within each mode: a fingerprint centred on the failing molecule or site, farthest point sampling, spread over models, cell sizes and temperatures.
- Take frames where the structure is still recognisable. A fully collapsed frame costs DFT time and teaches little, since the next model only needs to learn that the path there is uphill.

Before anything goes to DFT, an **independent review** by a fresh subagent or fresh code, so the selector's assumptions are not reused, verifies each frame: composition and charge neutrality, intact framework where expected, no unphysical contacts beyond the mode itself, forces in a sane range, no duplicates.
It also reads the selection against the ledger: every mode represented from several runs, the spread over models, cells and temperatures as planned, and no motif taking most of the budget without a failure to justify it.

The step is done when every ledger mode has its frames, or a stated reason for none, and every selected frame has passed the check.

## 5. Clean up

Keep the raw dumps until the selection is reviewed.
Then list them for deletion in one batch, keeping the run inputs, the reference frame, the logs and the event windows the selection came from.
If storage runs short earlier, list the dumps of runs with no event first, then of motifs that are already well covered.

## Delegation

The hunt splits into independent tasks: one MD batch, the scan of one batch, the review of step 4.
Hand those to subagents with lower capability and effort than the main session (a smaller model at medium effort does most of them), run them in parallel, and keep the ledger and the final selection in the main session.
