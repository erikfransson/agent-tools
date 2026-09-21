# Review: dynasor commit 5d4b66d ("initial test of ovito reader") vs master 3260689

Scope: single commit on branch `ovito-reader`, first (and only) commit past the merge-base
with master.
Adds two new files, no changes to existing code:

- `dynasor/trajectory/ovito_trajectory_reader.py` (120 lines, new `OvitoTrajectoryReader`)
- `tests/trajectory_reader/test_ovito_trajectory_reader.py` (212 lines, new tests)

Verification done: read both files in full against the existing reader implementations
(`ase_trajectory_reader.py`, `lammps_trajectory_reader.py`, `mdanalysis_trajectory_reader.py`)
and `abstract_trajectory_reader.py` / `trajectory_frame.py` for the conventions a reader is
expected to follow.
Ran the new test file (27 tests) against a read-only `git archive` copy of the commit; all
pass.
Wrote a synthetic triclinic LAMMPS dump and compared `OvitoTrajectoryReader` output against
the existing `LammpsTrajectoryReader` on the same file to check the cell convention (see
Finding 1).

## Finding 1 (bug, will silently corrupt non-orthogonal cells): cell is stored transposed

`_extract_cell` (line 67) does:

```python
return np.array(data.cell[:3, :3], dtype=float, copy=True)
```

OVITO's `SimulationCell` matrix stores the three lattice vectors **as columns** (its own docs:
"the first three columns a, b, c of the matrix are the vectors spanning the ... cell").
Every other reader in dynasor, and the `ReaderFrame` contract itself
(`dynasor/trajectory/trajectory_frame.py`, docstring: "cell — Simulation cell as 3 row
vectors"), uses **rows** as lattice vectors — see `ASETrajectoryReader` (`a.cell.array`, ASE's
row convention) and `LammpsTrajectoryReader`, which explicitly builds a row-vector matrix
(`cell[1,0]=xy`, `cell[2,0]=xz`, `cell[2,1]=yz`, i.e. `a=row0=(lx,0,0)`, `b=row1=(xy,ly,0)`,
`c=row2=(xz,yz,lz)`).

I confirmed this empirically: I built a synthetic triclinic LAMMPS dump (`xy=2, xz=1, yz=0.5`)
and read it with both readers. `OvitoTrajectoryReader` returned an **upper**-triangular cell
(tilt terms above the diagonal), `LammpsTrajectoryReader` returned a **lower**-triangular one
(tilt terms below the diagonal) — the two are transposes of each other in structure, exactly
as OVITO's column convention vs. dynasor's row convention predicts.

Downstream code assumes rows are lattice vectors (e.g.
`dynasor/trajectory/trajectory.py:272` logs `self.cell[0], self.cell[1], self.cell[2]` as a, b,
c; `dynasor/modes/atoms.py:45` computes reciprocal vectors as
`np.linalg.inv(cell).T`, which is only correct for a row-vector cell; q-point commensurability
checks in `correlation_functions.py` take `traj.cell` the same way).

This is invisible for every fixture used in the new tests, because all of them use orthogonal
(diagonal) cells, where a matrix equals its own transpose. It will produce silently wrong
results (wrong q-point commensurability, wrong reciprocal vectors) the moment this reader is
pointed at a sheared/triclinic cell, which is routine for NPT trajectories.

Fix: `data.cell[:3, :3].T` (or build the array directly with vectors as rows).

## Finding 2 (test-coverage gap that let Finding 1 through)

Every existing reader's test file (e.g. `tests/trajectory_reader/test_lammps_trajectory_reader.py`)
hardcodes an independently-parsed ground-truth array and asserts the reader reproduces it
exactly, atom by atom. `test_ovito_trajectory_reader.py` never does this: its checks are
shape/`np.isfinite`/frame-index/"is monotonic" checks, plus one relative check
(`test_unit_scaling_*`) that only compares the reader against *itself* run with two different
unit arguments. None of the 27 tests can distinguish correct output from output that is
internally self-consistent but wrong relative to the source file (e.g. a transposed cell, a
mis-ordered atom permutation, or a units mix-up that cancels in a ratio). A cross-check against
a value hand-computed from the raw file (as the LAMMPS/ASE test files do), or against the
existing `LammpsTrajectoryReader`/`ASETrajectoryReader` on a shared fixture with velocities and
a triclinic cell, would have caught Finding 1.

## Finding 3 (scope/integration, likely intentional for a first commit)

The new reader is not wired into anything: `dynasor/trajectory/trajectory.py`'s format
dispatch and `dynasor/trajectory/__init__.py` are both untouched, so `OvitoTrajectoryReader` is
unreachable through the public `Trajectory(...)` API and is only exercised by its own test
file. `ovito` is also not declared as a (optional) dependency anywhere in `pyproject.toml`.
Given the commit message ("initial test of ovito reader"), this reads as a deliberate spike
rather than an oversight, but it means the module is dead code from the package's point of
view until a follow-up wires it in and declares the dependency.

## Finding 4 (feature gap vs. sibling readers, minor for a spike)

Unlike `ASETrajectoryReader` and `MDAnalysisTrajectoryReader`, this reader never populates
`ReaderFrame.forces` or `ReaderFrame.atom_types`, even though OVITO commonly exposes both
(`Force`, `Particle Type`). Not a bug, just a smaller feature surface than its siblings.

## Finding 5 (minor, no test coverage)

The two `RuntimeError` branches (atom count changes between frames; particle identifiers
change between frames, in `__next__` and `_reorder_particles`) are not exercised by any test.
Low risk, but worth a quick regression test once a suitable fixture exists.

## Not a concern

- Unit handling (`set_unit_scaling_factors`, `x_factor`/`v_factor` application) matches the
  pattern used by every other reader and is exercised by `test_unit_scaling_*`.
- Iterator protocol (`StopIteration` on exhaustion, idempotent `close()`) matches sibling
  readers and is tested (`test_reader_stops_after_last_frame`).
- All fixture files referenced by the new tests already exist in
  `tests/trajectory_reader/trajectory_files/`, and the full new test file passes (27/27)
  when run against the commit.

## Bottom line

One real bug (cell transposed for non-orthogonal cells, Finding 1) should be fixed before this
reader is trusted on triclinic trajectories, and the test suite should gain at least one
ground-truth/cross-reader numeric check so a regression like it doesn't slip through silently
again. Everything else is normal for a first "spike" commit that isn't wired into the public
API yet.
