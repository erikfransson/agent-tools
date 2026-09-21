import numpy as np
import matplotlib.pyplot as plt

data = np.load("data.npz")
t = data["t"]
traces = data["traces"]
trace_noise = data["trace_noise"]
freq = data["freq"]
map_noise = data["map_noise"]
psd_delta = data["psd_delta"]

fig, axes = plt.subplot_mosaic(
    [["ts0", "map"], ["ts1", "map"], ["ts2", "map"]],
    figsize=(10, 6),
)

ts_axes = [axes["ts0"], axes["ts1"], axes["ts2"]]
for i, ax in enumerate(ts_axes):
    ax.plot(t, traces[i], color="C0", linewidth=0.8)
    ax.set_ylabel("signal")
    ax.set_title(f"noise = {trace_noise[i]:.3g}")
    if ax is ts_axes[-1]:
        ax.set_xlabel("t")
    else:
        ax.set_xticklabels([])

ax_map = axes["map"]
im = ax_map.pcolormesh(
    freq, map_noise, psd_delta, shading="auto", cmap="viridis"
)
ax_map.set_xlabel("frequency")
ax_map.set_ylabel("noise level")
ax_map.set_title("psd_delta (dB)")
fig.colorbar(im, ax=ax_map, label="dB")

fig.tight_layout()
fig.savefig("plain.png", dpi=150)
