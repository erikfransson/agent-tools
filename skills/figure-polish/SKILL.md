---
name: figure-polish
description: Conventions and QA for publication figures made with matplotlib/mplpub - fixed column widths, compact multi-panel layout, trying layout variants side by side, and looking at the rendered image before calling it done. Use whenever writing or editing a plotting script, changing a figure's layout, size, colour scale or panel arrangement, or before telling the user a figure is finished or looks good. Triggers on "plot", "figure", "panel", "colorbar", "subplot", "savefig", "make a chart of", and on any request to fix, tweak or improve an existing figure.
---

# Figure polish

The conventions are **defaults, not laws**. Follow them unless the user asks for something else or the content needs it, and say which you did and why. A stated preference wins immediately.

The verification rule is different. It is about not claiming something you have not checked, so it holds regardless.

If the repo carries its own style notes (a `PLOT_STYLE.md`, a study `CLAUDE.md`), those win over the defaults here.

## 1. Fixed widths

Figure width is **3.4 inches** (single column) or **6.6 inches** (double column). Height is free.

```python
import mplpub
mplpub.setup()
fig, ax = plt.subplots(figsize=(3.4, 2.8), dpi=300)
```

More panels means **shorter panels, not a wider figure**.
A four-panel row is `figsize=(6.6, 1.9)`, never `(13, 3.4)`.
Widening shrinks every font relative to the page.
If the content genuinely cannot fit, say so and ask.

Within that width, the data should be **as large as it can be**. Whitespace, duplicated labels and fat colorbars are area stolen from the panels.

- **Axis labels start with a capital.** `Time (ps)`, `Signal`, `Noise level $\sigma$`, not `time` or `signal`.
- **Share axis labels across a grid.** Only the bottom row gets the x label, only the left column the y label.
  Same for tick labels (`sharex`, `sharey`).
  One legend for the whole figure, not one per panel.
- **`fig.align_ylabels()` on any multi-panel figure**, and `fig.align_xlabels()` when several panels carry x labels.
- Thin colorbar: `fig.colorbar(..., aspect=40)` or higher.
- Trim padding, but stop before the panels touch.
- **No figure title.** The caption carries it. Put the identifying detail in the filename.
- **Leave `fontsize=` alone.** `mplpub.setup()` already sizes everything consistently.
  Set one only where a specific piece of text needs it, in the parameter block with the reason, and drop a point or two, not five.
  Break a long annotation over two lines before shrinking it.
- **Label multi-panel figures `a)`, `b)`, `c)`**, upper left *inside* each panel, `transform=ax.transAxes`, `va='top'`, letters from an iterator.
  Any short identifier the panel needs goes on the same line: `a) 500 K`, `e) 50\%` (mplpub sets usetex, so escape `%`).
  If data sits there, nudge it, staying near the upper left.
  On a heatmap give it a white box or a white halo so it reads on any colour.

## 2. Try variants side by side

A layout question (spacing, colorbar placement, panel size, legend position, tick density) rarely resolves in one guess, and one guess per round trip is the slow way.
Instead, when a choice is open, render a few options in one go, each to its own file, tile them into one contact sheet with a label per tile, and look at that.
Pick, keep the winner in the script, delete the rest.
Report what you compared and why the winner won in one or two lines, so the user can overrule with one word rather than re-run the loop.

A second pair of eyes helps when you have stared at the same figure for a while: hand the contact sheet to a subagent with the checklist below and the specific question, and read its answer as a report, not a verdict.
You still look at the final render yourself before claiming anything.

## 3. Look at it before saying it is good

Never report a figure as finished, correct, or looking good without having viewed the rendered image in this conversation.

```bash
MPLBACKEND=Agg python plot_thing.py
pdftoppm -png -r 100 thing.pdf /tmp/thing    # or: magick -density 100 thing.pdf thing.png
                                             # ImageMagick 6 spells magick as convert
```

Then Read the PNG.
If it cannot be rendered or read, say the figure is unverified.

One whole-figure render at 100-200 dpi shows the layout, not whether a label touches a line.
Follow it with a render at 400-600 dpi cropped to a couple of panels at a time (`PIL.Image.crop`).
For a local change, crop around the changed element and every immediate boundary: neighbouring axes, spines, labels, canvas edge.
Re-render after every layout change.
Layout bugs do not show up in the code.

## Checklist when looking

- Axis labels, tick labels and panel labels fully inside the canvas.
- Every panel label, annotation and legend sits inside its own axes and clear of the data. A legend may cover empty plot area, never data or guide lines.
- Text legible at the real width. If it looks small in the PNG it is worse on paper.
- Colour scale spans the data. If most of the plot is one flat colour, set the limits by hand.
- Panels meant to be compared share one colour scale and one axis range. Panels not meant to be compared visibly do not.
- Diverging data (anything signed) uses a symmetric scale and a diverging colormap, with zero white.
- Aspect ratio correct where the axes are physically commensurate.
- No overlapping ticks, no colorbar crowding the neighbouring panel.
- Tick labels carry as few decimals as the data needs, usually 1-2, the same count on every panel sharing that axis.
- Gaps between panels equal, and between panels and colorbars equal, measured in the rendered PNG.

## Gotchas

- For a figure with colorbars, place panels by hand with `fig.add_axes` or `GridSpec` with explicit ratios.
  `layout='constrained'` sizes each column around its own tick labels, so panels whose tick widths differ come out unevenly spaced, and it gives asymmetric gaps around a colorbar.
  `tight_layout()` ignores a shared colorbar and clips it.
  Constrained layout is fine for a quick look.
- A colorbar next to an axes with `set_aspect('equal')` is sized to the *cell*, not to the shrunken panel, so it overhangs.
  Fix it by choosing a figure height that makes the cells square.
  Deriving that height as `width / ncols * nrows` is wrong: the panel is narrower than `width / ncols` because the y-label column and the colorbar come out of the same width.
  Use `panel = (width - labels - colorbar) / ncols`, then `height = nrows * panel + bottom_margin`.
  Symptom: whitespace between rows plus a colorbar taller than the panels.
  Suspect the height, not the bar.
- When repositioning an axes across a `fig.canvas.draw()`, compute the final position once.
  A shift applied before and after the draw lands twice.
- Assign the mappable (`im = ax.imshow(...)`) before `fig.colorbar(im, ...)`, and run the script before reviewing layout.
- Under mplpub's usetex, `$\Gamma$` renders as a black box; `$\mathsf{\Gamma}$` works. Nothing errors, so only the render shows it.
- Vector PDF for line plots. PNG at 300 dpi or well above for heatmaps and dense scatter. Pick on file size, and follow the project's convention where one exists.
