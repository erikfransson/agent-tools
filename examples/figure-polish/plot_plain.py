import numpy as np
import matplotlib.pyplot as plt

data = np.load("data.npz")
x = data["x"]
y = data["y"]
potential = data["potential"]
residual = data["residual"]
t = data["t"]
msd = data["msd"]
energy = data["energy"]
displacement = data["displacement"]

fig, axes = plt.subplots(2, 2, figsize=(10, 8))

ax = axes[0, 0]
im = ax.pcolormesh(x, y, potential, shading="auto", cmap="viridis")
fig.colorbar(im, ax=ax, label="potential")
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.set_title("a) potential")

ax = axes[0, 1]
ax2 = ax.twinx()
l1, = ax.plot(t, msd, color="tab:blue", label="msd")
l2, = ax2.plot(t, energy, color="tab:red", label="energy")
ax.set_xlabel("t")
ax.set_ylabel("msd", color="tab:blue")
ax2.set_ylabel("energy", color="tab:red")
ax.legend(handles=[l1, l2], loc="best")
ax.set_title("b) time series")

ax = axes[1, 0]
ax.hist(displacement, bins=50, color="tab:green")
ax.set_xlabel("displacement")
ax.set_ylabel("count")
ax.set_title("c) displacement histogram")

ax = axes[1, 1]
im = ax.pcolormesh(x, y, residual, shading="auto", cmap="coolwarm")
fig.colorbar(im, ax=ax, label="residual")
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.set_title("d) residual")

fig.tight_layout()
fig.savefig("plain.png", dpi=150)
