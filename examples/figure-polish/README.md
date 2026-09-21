# figure-polish: the same request, with and without the skill

One loosely written request, two independent Sonnet agents, the same data.
`make_data.py` writes `data.npz`: one periodic signal sampled at three noise levels, and the noise-induced change in its power spectral density over 48 noise levels.

```
make a figure, 2 columns, left column is a 3x1 stack of the signal time series
at the 3 noise levels, right column is one big heatmap of psd_delta vs
frequency and noise level, data is in data.npz
```

With the skill, the three rows share one y range, so the noise really does grow from a) to c), and they share one time axis, one y label and no per-row titles.
The signed PSD change gets a diverging colormap symmetric about zero instead of a sequential one, and the whole figure is 6.6 inches wide rather than 15, so the fonts survive being placed in a column.
Without it, each row autoscales to its own range and the top two look about equally noisy, which is the one thing the figure exists to show.

Without the skill, [`plot_plain.py`](plot_plain.py):

![figure without the skill](plain.png)

With the skill loaded, [`plot_polished.py`](plot_polished.py):

![figure with the skill](polished.png)

## Reproduce

```
python3 make_data.py
MPLBACKEND=Agg python3 plot_plain.py
MPLBACKEND=Agg python3 plot_polished.py
```

`plot_polished.py` needs [mplpub](https://gitlab.com/materials-modeling/mplpub) and a working LaTeX installation, since mplpub sets `usetex`.
