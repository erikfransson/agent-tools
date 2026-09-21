import numpy as np
import matplotlib.pyplot as plt
import mplpub

# parameters
infile = 'data.npz'
outfile = 'polished.png'
dpi = 300
fig_width = 6.6       # double-column
left_margin = 0.55    # for y label + up to 4-digit tick labels (panel c)
right_margin = 0.50   # room for panel d) colorbar
mid_gap = 1.05        # room for panel a) colorbar + tick labels, and panel b)'s tick labels
top_margin = 0.08     # no title
row_gap = 0.42         # room for panel a)/b) tick labels
bottom_margin = 0.40  # for x label + tick labels
cbar_width = 0.07
cbar_pad = 0.10

mplpub.setup()

d = np.load(infile)
x, y = d['x'], d['y']
potential, residual = d['potential'], d['residual']
t, msd, energy = d['t'], d['msd'], d['energy']
displacement = d['displacement']

panel = (fig_width - left_margin - mid_gap - right_margin) / 2
fig_height = 2 * panel + top_margin + row_gap + bottom_margin

fig = plt.figure(figsize=(fig_width, fig_height))


def axes_rect(col, row):
    x0 = left_margin + col * (panel + mid_gap)
    y0 = bottom_margin + (1 - row) * (panel + row_gap)
    return [x0 / fig_width, y0 / fig_height, panel / fig_width, panel / fig_height]


ax_a = fig.add_axes(axes_rect(0, 0))
ax_b = fig.add_axes(axes_rect(1, 0))
ax_c = fig.add_axes(axes_rect(0, 1))
ax_d = fig.add_axes(axes_rect(1, 1))

extent = [x.min(), x.max(), y.min(), y.max()]

# a) potential heatmap
vlim_a = np.abs(potential).max()
im_a = ax_a.imshow(potential, extent=extent, origin='lower', aspect='equal',
                    cmap='RdBu_r', vmin=-vlim_a, vmax=vlim_a)
ax_a.set_xlabel(r'$x$')
ax_a.set_ylabel(r'$y$')
cax_a = fig.add_axes([(left_margin + panel + cbar_pad) / fig_width,
                       axes_rect(0, 0)[1],
                       cbar_width / fig_width,
                       panel / fig_height])
fig.colorbar(im_a, cax=cax_a)
ax_a.text(0.05, 0.95, 'a) potential', transform=ax_a.transAxes, va='top', ha='left',
          bbox={'facecolor': 'white', 'alpha': 0.7, 'pad': 1.5, 'edgecolor': 'none'})

# b) time series: msd and energy share a time axis but not a scale
l1, = ax_b.plot(t, msd, color=mplpub.tableau['blue'], label='MSD')
ax_b.set_xlabel(r'$t$')
ax_b.set_ylabel(r'MSD')
ax_b2 = ax_b.twinx()
l2, = ax_b2.plot(t, energy, color=mplpub.tableau['orange'], label='energy')
ax_b2.set_ylabel(r'energy')
ax_b2.legend(handles=[l1, l2], loc='upper left', bbox_to_anchor=(0.0, 0.88),
             frameon=True, facecolor='white', edgecolor='none', framealpha=0.9,
             handlelength=1.5, borderaxespad=0.1)
ax_b.text(0.05, 0.98, 'b)', transform=ax_b.transAxes, va='top', ha='left')

# c) histogram of displacement
ax_c.hist(displacement, bins=40, color=mplpub.tableau['blue'])
ax_c.set_xlabel(r'displacement')
ax_c.set_ylabel(r'count')
ax_c.text(0.85, 0.95, 'c)', transform=ax_c.transAxes, va='top', ha='right')

# d) residual heatmap
vlim_d = np.abs(residual).max()
im_d = ax_d.imshow(residual, extent=extent, origin='lower', aspect='equal',
                    cmap='RdBu_r', vmin=-vlim_d, vmax=vlim_d)
ax_d.set_xlabel(r'$x$')
ax_d.set_ylabel(r'$y$')
cax_d = fig.add_axes([(left_margin + panel + mid_gap + panel + cbar_pad) / fig_width,
                       axes_rect(1, 1)[1],
                       cbar_width / fig_width,
                       panel / fig_height])
fig.colorbar(im_d, cax=cax_d)
ax_d.text(0.05, 0.95, 'd) residual', transform=ax_d.transAxes, va='top', ha='left',
          bbox={'facecolor': 'white', 'alpha': 0.7, 'pad': 1.5, 'edgecolor': 'none'})

fig.align_ylabels([ax_a, ax_c])
fig.align_ylabels([ax_b, ax_d])
fig.align_xlabels([ax_a, ax_c, ax_b, ax_d])

plt.savefig(outfile, dpi=dpi)
