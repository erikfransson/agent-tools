# Review of commit 5d4b66d

## Comment

This commit ("initial test of ovito reader") adds a new, self-contained
`OvitoTrajectoryReader` plus its test file. It is not yet wired into
`Trajectory`'s reader factory, `dynasor/trajectory/__init__.py`, docs, or
`pyproject.toml` dependencies, consistent with the commit message describing it
as a first test rather than a finished integration.

### Major (Blocking)

1. **Cell matrix is transposed for any non-orthogonal cell.**
   `dynasor/trajectory/ovito_trajectory_reader.py:66-67` (`_extract_cell`)
   returns `data.cell[:3, :3]` unchanged. OVITO's `SimulationCell` stores the
   lattice vectors **a, b, c as columns** of its 3x4 matrix, while dynasor's
   convention (see the `ReaderFrame` docstring, and how
   `ase_trajectory_reader.py`/`lammps_trajectory_reader.py` build `cell`) is
   lattice vectors **as rows**. For an orthogonal (diagonal) cell the
   transpose is invisible, which is why none of the 5 test fixtures (all
   orthogonal) catch it; for a triclinic/tilted cell the shear components end
   up transposed, silently producing a geometrically different simulation
   cell.
   Reproduced directly: an ASE `Atoms` with cell rows
   `[[10,0,0],[1,8,0],[2,3,6]]`, written to extxyz and opened with
   `ovito.io.import_file`, gives `data.cell[:3,:3] ==
   [[10,1,2],[0,8,3],[0,0,6]]` — the transpose of the input. Fix:
   `data.cell[:3, :3].T`.

2. **Duplicate Particle Identifiers cause silent atom-identity swapping.**
   `ovito_trajectory_reader.py:69-87` (`_reorder_particles`) validates
   cross-frame consistency only by comparing *sorted id values*, not their
   uniqueness. If two atoms share an id, `argsort`'s tie-breaking (row order)
   becomes an implicit, arbitrary identity mapping across frames, and no
   error is raised.
   Reproduced with a synthetic 3-atom lammpstrj (ids `[1, 1, 2]`) where the
   two id-1 atoms swap row order between frame 0 and frame 1: the returned
   `positions` for frame 1 come back with those two atoms' coordinates
   silently swapped, no exception. Dynasor's currently-supported dump formats
   normally guarantee unique ids, so this is a narrower, defensive-coding gap
   rather than a commonly hit path, but it fails silently rather than loudly.

3. **The per-atom reorder mechanism has no effective test coverage.**
   None of the 5 fixtures ever changes an atom's row order between frames:
   the 3 `.xyz` fixtures carry no Particle Identifier at all (so
   `_has_ids=False` and reordering is skipped outright), and both
   `.lammpstrj` fixtures keep ids in ascending file order in every frame.
   Confirmed by disabling `_reorder_particles` (returning the raw,
   unreordered array) in an extracted copy of this commit: all 27 tests still
   pass. The reordering logic — arguably the main reason to hand-write this
   reader rather than reuse MDAnalysis/ASE — is therefore unprotected against
   regression, and is also what lets finding 2 go undetected.
   Suggested fix: one small hand-built lammpstrj fixture (2 frames, a few
   atoms, ids reordered between frames), in the same style as the
   `tmp_path`-based minimal fixtures already used in
   `test_lammps_trajectory_reader.py`; no new binary fixture needed.

### Minor (Not-blocking)

1. `atom_types` is never set on the returned `ReaderFrame`, unlike
   `extxyz_trajectory_reader.py`, even though `data.particles['Particle
   Type']` is available at the same point positions/velocities are read.
   `Trajectory.__init__` requires `frame0.atom_types is not None` for
   `atomic_indices='read_from_trajectory'` (`trajectory.py:165`), so this
   reader cannot support that documented option as written.
2. The atom-count-changed and particle-id-changed `RuntimeError` paths have
   no test coverage. Triggering both manually confirms the logic itself is
   correct — this is a coverage gap, not a bug.
3. Velocity-property detection (`'Velocity'` vs `'vel'`) runs once from frame
   0 and is assumed to hold for every later frame. If a later frame lacks
   that property, `__next__` raises an unhandled OVITO `KeyError`
   (`"Property 'vel' does not exist in container."`) instead of the clean
   `RuntimeError` style used for the atom-count/id checks. Reproduced with a
   2-frame extxyz file whose second frame drops `vel`.
4. Tests only check relative unit-scaling ratios (`test_unit_scaling_*`) and
   shape/finiteness (`assert_valid_frame`); none asserts an absolute
   position/velocity/cell value against the known fixture content, unlike
   `test_lammps_trajectory_reader.py`/`test_extxyz_trajectory_reader.py`,
   which hardcode a literal expected array (`first_frame`) and assert
   `np.allclose` against it. Since this reader reuses
   `positions_and_velocities.lammpstrj`, the same literal array could be
   reused almost verbatim.
5. `__init__` calls `self._pipeline.compute(0)` to inspect the first frame,
   and the first `__next__` call (`self._frame == 0`) computes frame 0 again.
   The sibling readers avoid this (they lazily parse the first frame exactly
   once); likely cheap here, but reader-specific and easy to avoid by caching
   the first `compute(0)` result.
6. `_extract_cell` is a one-line, stateless private method called exactly
   once; simpler inlined into `__next__`, matching how sibling readers build
   the cell inline.
7. `_reorder_particles`'s argsort-based cross-frame id matching duplicates,
   conceptually, the ad hoc reorder-by-id logic already in
   `lammps_trajectory_reader.py:130-168` (different guarantees/validation, no
   shared helper). Not necessary to unify for an "initial test" commit, but a
   reasonable candidate for `AbstractTrajectoryReader` if a third reader ever
   needs the same pattern.
8. Not registered in `Trajectory`'s reader factory, `dynasor/trajectory/__init__.py`,
   docs, or `pyproject.toml` dependencies. Consistent with the commit message;
   noted for completeness, not a defect in this commit.

## Internal findings

**Reviewed range:** base `3260689` (= merge-base with `master`) → head
`5d4b66d`. Single commit, two new files (120 + 212 lines), no existing file
touched.

**Verification performed by the lead reviewer:**
- `git archive 5d4b66d` exported into a scratch directory outside the
  dynasor checkout; `pytest` run from there (`nice -n 10`,
  `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`): **27/27 passed**.
- `flake8` (using the repo's own `setup.cfg`) on both new files: clean.
- Manually hand-traced the `_reorder_particles` scatter/argsort logic on a
  3-atom permuted example: the reordering algorithm itself (for unique ids)
  is correct.
- Confirmed OVITO's cell-matrix column convention directly against ASE's
  row convention (Major finding 1) with a purpose-built triclinic test file.
- Confirmed the duplicate-id silent-swap scenario (Major finding 2) and the
  cross-frame velocity-property KeyError (Minor finding 3) each with a small
  synthetic trajectory file, run against the extracted commit snapshot.
- Confirmed `test_lammps_trajectory_reader.py` hardcodes literal expected
  arrays and asserts `np.allclose` against them (basis for Minor finding 4).
- Confirmed via `git show`/reads that `OvitoTrajectoryReader` is absent from
  `trajectory.py`'s factory, `dynasor/trajectory/__init__.py`, and
  `pyproject.toml` dependencies.

**Sub-agent reports** (three initial reviewers, `general-purpose`/Sonnet,
run in parallel against the same read-only commit snapshot; their leads were
independently checked by the lead reviewer above before inclusion):

- *Structure/simplification*: flagged the missing `atom_types` (folded into
  Minor 1), the `_extract_cell` wrapper (Minor 6), the ad hoc reorder
  duplication vs. `lammps_trajectory_reader.py` (Minor 7), and the
  double-compute of frame 0 (Minor 5). Confirmed non-integration is
  consistent with "initial test" and not a required fix here.
- *Correctness bug-hunt*: found and reproduced the duplicate-Particle-Identifier
  silent swap (Major 2) and the cross-frame velocity-property `KeyError`
  (Minor 3); ruled out dtype issues, 0-atom/0-frame edge cases (fail inside
  `import_file` itself), and reentrancy (no `prefetch.py` consumption pattern
  in this checkout applies here).
- *Test coverage*: independently confirmed (via a mutation test — disabling
  the reorder logic entirely and rerunning the suite) that the id-based
  reorder path is never exercised beyond its identity-permutation case
  (Major 3); confirmed the `RuntimeError` paths are untested (Minor 2) and
  the absence of absolute-value assertions (Minor 4).

**Rejected/downgraded leads:** none of the sub-agent leads were rejected outright;
severities above reflect the lead reviewer's own calibration (e.g. the
duplicate-id issue is real and reproduced but likely narrow in practice, so
kept as Major on the strength of the reproduction rather than likelihood).

No GitLab MR exists for this commit range, so no MR description/discussion
review, posting, or thread resolution applies.
