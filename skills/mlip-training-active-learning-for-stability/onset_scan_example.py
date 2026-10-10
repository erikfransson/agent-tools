"""Example onset scan for one MD trajectory: a starting point to adapt, not a finished tool.

    python3 onset_scan_example.py dump.xyz

Per frame it records the shortest distance per element pair, the volume per atom,
and whether the heavy-atom bond graph still matches the first frame.
A frame is physical while every pair distance sits above its floor, the volume stays within
a band around frame 0, and (optionally) no heavy-atom bond has formed or broken.
The onset is the first unphysical frame, and the frames just before it are the candidates for DFT.

Adapt per system: the distance floors (calibrate by plotting the per-pair curves of a few runs,
a floor too tight catches normal thermal motion), the bond cutoffs, a persistence rule for
events that recover, and further channels (coordination, desorption height, fusion, temperature).
"""
import sys
import numpy as np
import pandas as pd
from ase.io import iread
from ase.neighborlist import neighbor_list, natural_cutoffs

# parameters
trajectory_file = sys.argv[1] if len(sys.argv) > 1 else 'dump.xyz'
n_before = 5                     # candidate frames kept before the onset
volume_limit = 6.0               # allowed change in volume per atom vs frame 0 (Å^3)
check_bond_graph = True          # heavy-atom bonds formed or broken vs frame 0
bond_cutoff_scale = 1.25         # x natural (covalent) radii
heavy_bonded = {'C', 'N', 'O', 'S'}   # elements whose mutual bonds define the molecules

shortest_distances_allowed = {   # example floors for a lead-iodide hybrid perovskite (Å)
    ('C', 'C'): 1.80, ('C', 'H'): 0.75, ('C', 'I'): 2.1, ('C', 'N'): 0.90, ('C', 'Pb'): 2.6,
    ('H', 'H'): 1.0, ('H', 'I'): 1.80, ('H', 'N'): 0.70, ('H', 'Pb'): 2.2, ('I', 'I'): 2.5,
    ('I', 'N'): 2.1, ('I', 'Pb'): 2.50, ('N', 'N'): 1.4, ('N', 'Pb'): 2.4, ('Pb', 'Pb'): 4.1,
}
max_floor = max(shortest_distances_allowed.values())


def bond_set(atoms):
    heavy = np.array([s in heavy_bonded for s in atoms.get_chemical_symbols()])
    i, j = neighbor_list('ij', atoms, [c * bond_cutoff_scale for c in natural_cutoffs(atoms)])
    keep = heavy[i] & heavy[j] & (i < j)
    return set(zip(i[keep], j[keep]))


records = []
for frame, atoms in enumerate(iread(trajectory_file, index=':')):
    symbols = np.array(atoms.get_chemical_symbols())
    # pairs within the largest floor are enough to find every violation (O(N), unlike all distances)
    i, j, d = neighbor_list('ijd', atoms, max_floor + 0.5)
    row = {'frame': frame, 'time': float(atoms.info.get('Time', frame)),
           'volume': atoms.get_volume() / len(atoms)}
    for a, b in shortest_distances_allowed:
        mask = ((symbols[i] == a) & (symbols[j] == b)) | ((symbols[i] == b) & (symbols[j] == a))
        row[f'{a}-{b}'] = d[mask].min() if mask.any() else np.inf
    if check_bond_graph:
        bonds = bond_set(atoms)
        if frame == 0:
            bonds0 = bonds
        row['bonds_changed'] = len(bonds ^ bonds0)
    records.append(row)

df = pd.DataFrame(records)
floors = pd.Series({f'{a}-{b}': v for (a, b), v in shortest_distances_allowed.items()})
ok_dist = (df[floors.index] > floors).all(axis=1)
ok_vol = (df['volume'] - df['volume'].iloc[0]).abs() < volume_limit
ok_bond = df['bonds_changed'] == 0 if check_bond_graph else True
df['physical'] = ok_dist & ok_vol & ok_bond
df.to_csv(trajectory_file.rsplit('.', 1)[0] + '_onset_scan.csv', index=False)

bad = np.flatnonzero(~df['physical'].to_numpy())
if len(bad) == 0:
    print(f'{len(df)} frames, no violation')
    sys.exit()
onset = bad[0]
row = df.iloc[onset]
channels = [p for p in floors.index if row[p] <= floors[p]]
if not ok_vol.iloc[onset]:
    channels.append('volume')
if check_bond_graph and row['bonds_changed']:
    channels.append(f'bond graph ({row["bonds_changed"]:.0f} bonds changed)')
print(f'{len(df)} frames, onset at frame {onset} (time {row["time"]:.1f}), channels: {", ".join(channels)}')
print(f'candidate frames for DFT: {list(range(max(0, onset - n_before), onset))}')
