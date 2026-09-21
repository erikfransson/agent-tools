import numpy as np

# parameters
seed = 0
grid = 96
nsteps = 4000
dt = 0.002
nsamples = 50000
outfile = 'data.npz'

rng = np.random.default_rng(seed)

x = np.linspace(-3, 3, grid)
y = np.linspace(-3, 3, grid)
X, Y = np.meshgrid(x, y)
potential = np.exp(-(X**2 + Y**2) / 2) * np.cos(2 * X) + 0.15 * rng.standard_normal((grid, grid))
residual = potential - np.exp(-(X**2 + Y**2) / 1.6) * np.cos(2 * X - 0.3)

t = np.arange(nsteps) * dt
msd = 0.42 * t + 0.03 * np.cumsum(rng.standard_normal(nsteps)) * np.sqrt(dt)
energy = -4.31 + 0.06 * rng.standard_normal(nsteps) + 0.02 * np.sin(2 * np.pi * t / 1.3)

displacement = rng.gamma(2.4, 0.11, nsamples)

np.savez(outfile, x=x, y=y, potential=potential, residual=residual,
         t=t, msd=msd, energy=energy, displacement=displacement)
print(f'{outfile}: potential {potential.shape}, residual {residual.shape} '
      f'in [{residual.min():.2f}, {residual.max():.2f}], t {t.shape}, '
      f'displacement {displacement.shape}')
