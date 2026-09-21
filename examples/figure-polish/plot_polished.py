import numpy as np
import matplotlib.pyplot as plt
import mplpub

# parameters
infile = 'data.npz'
outfile = 'polished.png'
dpi = 300
fig_w, fig_h = 6.6, 2.85
left_margin = 0.55      # space for left-column y ticks/label
ts_width = 2.15         # width of the time-series column
mid_gap = 0.62          # gap between time-series column and heatmap (room for heatmap y ticks)
map_width = 2.56        # width of the heatmap panel
cbar_gap = 0.10         # gap between heatmap and colorbar
cbar_width = 0.12       # colorbar width
right_margin = 0.42     # space for colorbar tick labels
bottom_margin = 0.42    # space for shared x label/ticks
top_margin = 0.06
row_gap = 0.05           # gap between the 3 stacked time-series panels
line_color = '#1F77B4'

mplpub.setup(width=fig_w, height=fig_h)

d = np.load(infile)
t, traces, trace_noise = d['t'], d['traces'], d['trace_noise']
freq, map_noise, psd_delta = d['freq'], d['map_noise'], d['psd_delta']

fig = plt.figure(figsize=(fig_w, fig_h), dpi=dpi)

# --- left column: 3 stacked time series, sharing x ---
stack_h = fig_h - bottom_margin - top_margin
panel_h = (stack_h - 2 * row_gap) / 3
ymin, ymax = traces.min(), traces.max()
pad = 0.08 * (ymax - ymin)

axes_ts = []
for i in range(3):
    y0 = bottom_margin + i * (panel_h + row_gap)
    ax = fig.add_axes([left_margin / fig_w, y0 / fig_h,
                        ts_width / fig_w, panel_h / fig_h])
    axes_ts.append(ax)

letters = ['c)', 'b)', 'a)']  # bottom-to-top fill order, top panel is a)
for i, ax in enumerate(axes_ts):
    j = 2 - i  # top panel (i=2) shows the lowest noise level, trace index 0
    ax.plot(t, traces[j], color=line_color, lw=0.6)
    ax.set_ylim(ymin - pad, ymax + pad)
    ax.set_xlim(t[0], t[-1])
    ax.text(0.02, 0.95, f'{letters[i]} $\\sigma={trace_noise[j]:.2f}$',
            transform=ax.transAxes, va='top', ha='left')
    if ax is not axes_ts[0]:
        ax.set_xticklabels([])

axes_ts[0].set_xlabel('Time')
fig.text(0.01, bottom_margin / fig_h + stack_h / fig_h / 2, 'Signal',
         rotation='vertical', va='center', ha='left')

# --- right column: one heatmap of psd_delta vs freq and noise level ---
ax_map = fig.add_axes([(left_margin + ts_width + mid_gap) / fig_w, bottom_margin / fig_h,
                        map_width / fig_w, stack_h / fig_h])
ax_cbar = fig.add_axes([(left_margin + ts_width + mid_gap + map_width + cbar_gap) / fig_w,
                         bottom_margin / fig_h, cbar_width / fig_w, stack_h / fig_h])

vmax = np.abs(psd_delta).max()
im = ax_map.pcolormesh(freq, map_noise, psd_delta,
                        cmap='RdBu_r', vmin=-vmax, vmax=vmax, shading='nearest')
ax_map.set_yscale('log')
ax_map.set_xlabel('Frequency')
ax_map.set_ylabel('Noise level $\\sigma$')
ax_map.text(0.02, 0.97, 'd)', transform=ax_map.transAxes, va='top', ha='left',
            bbox=dict(boxstyle='square,pad=0.1', fc='white', ec='none', alpha=0.8))

cbar = fig.colorbar(im, cax=ax_cbar)
cbar.set_label('PSD change (dB)')

fig.align_ylabels(axes_ts + [ax_map])

fig.savefig(outfile, dpi=dpi)
print(f'wrote {outfile}')
