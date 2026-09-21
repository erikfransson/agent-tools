import numpy as np

# parameters
seed = 0
dt = 0.01
nsteps = 2048
amplitudes = [0.80, 0.35]
frequencies = [1.5, 4.2]
trace_noise = [0.05, 0.25, 1.00]
map_noise = np.logspace(np.log10(0.02), np.log10(1.5), 48)
fmax = 10.0
outfile = 'data.npz'

rng = np.random.default_rng(seed)

t = np.arange(nsteps) * dt
clean = sum(a * np.sin(2 * np.pi * f * t) for a, f in zip(amplitudes, frequencies))

traces = np.array([clean + s * rng.standard_normal(nsteps) for s in trace_noise])

freq_all = np.fft.rfftfreq(nsteps, dt)
keep = freq_all <= fmax
freq = freq_all[keep]


def psd(x):
    return np.abs(np.fft.rfft(x))**2 / nsteps


psd_clean = psd(clean)[keep]
floor = 1e-6
psd_delta = np.array([
    10 * np.log10((psd(clean + s * rng.standard_normal(nsteps))[keep] + floor)
                  / (psd_clean + floor))
    for s in map_noise])

np.savez(outfile, t=t, clean=clean, traces=traces, trace_noise=trace_noise,
         freq=freq, map_noise=map_noise, psd_delta=psd_delta)
print(f'{outfile}: traces {traces.shape} at noise {trace_noise}, '
      f'signal range [{traces.min():.2f}, {traces.max():.2f}], '
      f'psd_delta {psd_delta.shape} in [{psd_delta.min():.1f}, {psd_delta.max():.1f}] dB, '
      f'freq up to {freq[-1]:.1f}')
