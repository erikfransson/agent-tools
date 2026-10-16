"""Example gate and summary for an initial dataset: a starting point to adapt, not a finished tool.

    python3 verify_dataset_example.py structures/*.xyz > dataset_report.md

Per structure it checks the atom count, the shortest distance per element pair against a floor,
whether the cell holds a vacuum gap (finite system), and near-duplicates by composition and the sorted
neighbour-distance fingerprint.
It then prints a markdown table, counts per family, an atom-count summary and a temperature histogram.

Adapt per system: the floors (default a fraction of the summed covalent radii, replace with measured
values once a few clean thermal frames exist, about 0.9 of the shortest distance seen), a molecule-integrity
check, charge or stoichiometry rules, a density band, and connectivity labels (phase, coordination)
re-measured from the structure. H-H and anion-anion pairs (I-I, O-O, Cl-Cl) need measured floors:
the covalent default lets a fused I2 at 2.7 Å or an H2 at 0.5 Å through.
Contact files are exempt from the floor only for the pair named in their file name.
Finite detection scans fractional coordinates per axis, which is approximate for strongly skewed cells.
"""
import re
import sys
from collections import Counter, defaultdict
import numpy as np
from ase.data import covalent_radii, atomic_numbers
from ase.io import read
from ase.neighborlist import neighbor_list

# parameters
files = sys.argv[1:]
n_atoms_range = (1, 400)
floor_scale = 0.85                # floor = floor_scale * (r_cov(A) + r_cov(B)); override per pair below
floor_override = {('H', 'H'): 1.0}   # measured floors per pair, e.g. {('I', 'I'): 3.3, ('O', 'O'): 2.0}
vacuum_gap = 6.0                  # Å of empty space along any axis marks a finite system
duplicate_tol = 0.02              # Å, max difference of sorted neighbour distances for a duplicate
family_pattern = re.compile(r'_(prototype|strained|rattled|enumerated|surface|vacancy|interstitial|antisite|nano|MD|contact)_?')
contact_pattern = re.compile(r'_contact_([A-Z][a-z]?)([A-Z][a-z]?)-')
temperature_pattern = re.compile(r'_T(\d+)')


def floor_for(a, b):
    key = tuple(sorted((a, b)))
    if key in floor_override:
        return floor_override[key]
    return floor_scale * (covalent_radii[atomic_numbers[a]] + covalent_radii[atomic_numbers[b]])


def shortest_pairs(atoms, cutoff=4.0):
    symbols = np.array(atoms.get_chemical_symbols())
    i, j, d = neighbor_list('ijd', atoms, cutoff)
    out = {}
    for a, b, dist in zip(symbols[i], symbols[j], d):
        key = tuple(sorted((a, b)))
        out[key] = min(out.get(key, np.inf), dist)
    return out, np.sort(d)


def same_fingerprint(x, y):
    return len(x) == len(y) and (len(x) == 0 or np.abs(x - y).max() < duplicate_tol)


def is_finite(atoms):
    frac = atoms.get_scaled_positions(wrap=True)
    for axis in range(3):
        length = np.linalg.norm(atoms.cell[axis])
        x = np.sort(frac[:, axis]) * length
        gaps = np.diff(np.concatenate([x, [x[0] + length]]))
        if gaps.max() > vacuum_gap:
            return True
    return False


rows = []
seen = defaultdict(list)
for f in files:
    atoms = read(f)
    name = f.rsplit('/', 1)[-1].removesuffix('.xyz')
    fam = atoms.info.get('family') or (family_pattern.search(name).group(1) if family_pattern.search(name) else 'unknown')
    temp = atoms.info.get('T_target') or (int(temperature_pattern.search(name).group(1)) if temperature_pattern.search(name) else 0)
    exempt = tuple(sorted(contact_pattern.search(name).groups())) if contact_pattern.search(name) else None
    fails = []
    n = len(atoms)
    if not n_atoms_range[0] <= n <= n_atoms_range[1]:
        fails.append(f'natoms {n}')
    pairs, fingerprint = shortest_pairs(atoms)
    closest = ', '.join(f'{a}-{b} {d:.2f}' for (a, b), d in sorted(pairs.items()))
    for key, d in pairs.items():
        if key != exempt and d < floor_for(*key):
            fails.append(f'{key[0]}-{key[1]} {d:.2f} < {floor_for(*key):.2f}')
    if exempt and exempt not in pairs:
        fails.append('named contact pair not found')
    comp = atoms.get_chemical_formula()
    for other, other_fp in seen[comp]:
        if same_fingerprint(fingerprint, other_fp):
            fails.append(f'possible duplicate of {other}')
            break
    seen[comp].append((name, fingerprint))
    rows.append(dict(name=name, family=fam, natoms=n, T=temp, formula=comp, finite=is_finite(atoms),
                     closest=closest, fail='; '.join(fails)))

n_fail = sum(bool(r['fail']) for r in rows)
print(f'# Dataset verification\n\n{len(rows)} structures, {n_fail} failing hard checks.\n')
print('| name | family | N | T | formula | finite | closest pairs | fail |')
print('|:--|:--|--:|--:|:--|:--|:--|:--|')
for r in rows:
    print(f"| {r['name']} | {r['family']} | {r['natoms']} | {r['T']} | {r['formula']} | {'yes' if r['finite'] else ''} | {r['closest']} | {r['fail']} |")

print('\n## Summary\n\n| family | count | atoms min-max |\n|:--|--:|:--|')
by_family = defaultdict(list)
for r in rows:
    by_family[r['family']].append(r['natoms'])
for fam, ns in sorted(by_family.items()):
    print(f'| {fam} | {len(ns)} | {min(ns)}-{max(ns)} |')
ns = np.array([r['natoms'] for r in rows])
print(f'\nAtoms: median {int(np.median(ns))}, {(ns <= 300).sum()} of {len(ns)} at or below 300, max {ns.max()}.')
edges = [0, 1, 150, 300, 450, 600, 800, 1000, 1500, 5000]
hist = Counter(np.digitize([r['T'] for r in rows], edges[1:]))
print('\n| T bin (K) | static | ' + ' | '.join(f'{edges[k]}-{edges[k + 1]}' for k in range(1, len(edges) - 1)) + ' |')
print('|:--|' + '--:|' * (len(edges) - 1))
print('| count | ' + ' | '.join(str(hist.get(k, 0)) for k in range(len(edges) - 1)) + ' |')
if n_fail:
    print('\n## Failures\n')
    for r in rows:
        if r['fail']:
            print(f"- {r['name']}: {r['fail']}")
sys.exit(1 if n_fail else 0)
