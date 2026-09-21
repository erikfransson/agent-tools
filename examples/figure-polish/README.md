# figure-polish: the same request, with and without the skill

One sloppily written figure request, given to two independent Sonnet agents on the same data.
The first was told to write the plotting code the way it normally would.
The second was told to invoke the `figure-polish` skill and follow it, including its rule that nothing is reported as finished before the rendered image has been looked at.

`make_data.py` writes `data.npz`, the input for both scripts: a signed potential on a 96x96 grid, an MSD and energy trace over 4000 steps, a residual field, and 50000 displacement samples.

## Without the skill

```
plot a figure with 2x2 layout subplots, a) heatmap X, Y where Z is the potential,
b) is time-series data (msd and energy), c) is histogram of displacement and
d) is another heatmap with the residual, data is in data.npz
```

Produced by [`plot_plain.py`](plot_plain.py):

![figure without the skill](plain.png)

15 by 12 inches, so every font comes out tiny once the figure is scaled into a column.
A title on each panel duplicating what the axis or the caption already says.
Two fat colorbars, one of them on a signed field with a sequential colormap whose zero sits at no particular colour.
The MSD line, the point of panel b), is buried under 4000 steps of energy noise drawn on top of it.
Panel c) has no colorbar and panel a) does, so the two columns do not line up.

## With the skill

```
[figure-polish skill loaded]

plot a figure with 2x2 layout subplots, a) heatmap X, Y where Z is the potential,
b) is time-series data (msd and energy), c) is histogram of displacement and
d) is another heatmap with the residual, data is in data.npz
```

Produced by [`plot_polished.py`](plot_polished.py):

![figure with the skill](polished.png)

6.6 inches wide, the double-column width, at 300 dpi, with the panels placed by hand through `fig.add_axes` so the colorbars do not pull the columns out of alignment.
`mplpub.setup()` sizes the fonts, so they are legible at the real width and no `fontsize=` appears in the script.
Both signed fields get a diverging colormap on a scale symmetric about zero, with white at zero.
Panel letters sit inside the axes, clear of the data, with the quantity folded into the letter instead of a title.
Colorbars are thin, and the figure carries no title.

The script's own shape also differs: every margin, gap and colorbar width is a named parameter at the top, which is what made the five rounds of render-and-look cheap.

## Reproduce

```
python3 make_data.py
MPLBACKEND=Agg python3 plot_plain.py
MPLBACKEND=Agg python3 plot_polished.py
```

`plot_polished.py` needs [mplpub](https://gitlab.com/materials-modeling/mplpub) and a working LaTeX installation, since mplpub sets `usetex`.
