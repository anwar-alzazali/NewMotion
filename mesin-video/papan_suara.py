"""Efek suara sintetis (numpy) untuk papan: tanpa berkas luar, tanpa biaya.
campur(events, durasi, path_wav): events = [[detik, jenis, volume], ...]"""
import wave
import numpy as np

SR = 44100


def _env(n, atk=0.003, tau=0.08):
    t = np.arange(n) / SR
    return np.minimum(1, t / atk) * np.exp(-t / tau)


def _lp(x, a):  # lowpass satu kutub; a kecil = lebih gelap
    y = np.empty_like(x); s = 0.0
    for i, v in enumerate(x):
        s += a * (v - s); y[i] = s
    return y


def _noise(n, seed):
    return np.random.default_rng(seed).uniform(-1, 1, n)


def buat(jenis, seed=1):
    t = lambda d: np.arange(int(SR * d)) / SR
    if jenis == "pop":
        x = t(0.14); f = 700 * np.exp(-x * 14) + 250
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(x), 0.002, 0.04)
    if jenis == "thud":
        x = t(0.28); f = 120 * np.exp(-x * 9) + 55
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(x), 0.002, 0.07)
        n = _lp(_noise(len(x), seed), 0.18) * _env(len(x), 0.001, 0.02) * 0.6
        return s + n
    if jenis == "tick":
        x = t(0.05); n = _noise(len(x), seed) * _env(len(x), 0.0005, 0.004)
        b = np.sin(2 * np.pi * (1500 + 400 * (seed % 5)) * x) * _env(len(x), 0.0005, 0.008) * 0.5
        return (n - _lp(n, 0.05)) * 0.7 + b
    if jenis == "klik":
        x = t(0.08); return np.sin(2 * np.pi * 900 * x) * _env(len(x), 0.0005, 0.012) + _noise(len(x), seed) * _env(len(x), 0.0005, 0.005) * 0.5
    if jenis == "whoosh":
        x = t(0.55); n = _noise(len(x), seed); a = 0.05 + 0.5 * np.sin(np.pi * np.linspace(0, 1, len(x))) ** 2
        y = np.empty_like(n); s = 0.0
        for i in range(len(n)):
            s += a[i] * (n[i] - s); y[i] = s
        return y * np.sin(np.pi * np.linspace(0, 1, len(x))) ** 1.5 * 2.2
    if jenis == "swish":
        x = t(0.28); n = _noise(len(x), seed); y = n - _lp(n, 0.12)
        return y * np.sin(np.pi * np.linspace(0, 1, len(x))) ** 1.2 * 1.3
    if jenis == "ding":
        x = t(0.7); return (np.sin(2 * np.pi * 1320 * x) * np.exp(-x * 7) + 0.45 * np.sin(2 * np.pi * 1980 * x) * np.exp(-x * 10)) * 0.8
    if jenis == "notif":
        a = buat("ding"); b = np.zeros(int(SR * 0.9)); b[:len(a)] += a * 0.8
        x = t(0.7); c = (np.sin(2 * np.pi * 1760 * x) * np.exp(-x * 7) + 0.4 * np.sin(2 * np.pi * 2640 * x) * np.exp(-x * 11)) * 0.8
        o = int(SR * 0.12); b[o:o + len(c)] += c[:len(b) - o]; return b
    if jenis == "buzz":
        x = t(0.28); f = 150 + 20 * np.sin(x * 40)
        return np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.35 * np.minimum(1, x / 0.01) * np.exp(-x * 6)
    if jenis == "konfeti":
        x = t(0.5); n = _noise(len(x), seed); pop = np.sin(2 * np.pi * 330 * x) * np.exp(-x * 30)
        return pop * 0.9 + (n - _lp(n, 0.3)) * np.exp(-x * 7) * 0.8
    if jenis == "kilau":
        x = t(0.9); r = np.random.default_rng(seed); y = np.zeros(len(x))
        for k in range(7):
            o = int(r.uniform(0, 0.35) * SR); f = r.uniform(2400, 4800); d = x[: len(x) - o]
            y[o:] += np.sin(2 * np.pi * f * d) * np.exp(-d * 11) * 0.3
        return y
    # ---- suasana mencekam (seri misteri) ----
    if jenis == "dengung":  # dengung rendah 3 dtk yang naik-turun
        x = t(3.0); f = 46 + 3 * np.sin(2 * np.pi * 0.4 * x)
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR) + 0.25 * _lp(_noise(len(x), seed), 0.01) * 6
        return y * np.sin(np.pi * np.linspace(0, 1, len(x))) ** 0.8 * 0.6
    if jenis == "derit":  # pintu kayu berderit
        x = t(1.4); f = 520 + 260 * np.sin(2 * np.pi * 0.9 * x) + 60 * np.sin(2 * np.pi * 11 * x)
        kasar = (np.sin(2 * np.pi * 37 * x) > 0.3).astype(float) * 0.6 + 0.4
        y = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * kasar
        y = _lp(y, 0.12) - _lp(y, 0.01)
        return y * np.sin(np.pi * np.linspace(0, 1, len(x))) ** 0.6 * 1.4
    if jenis == "detak":  # detak jantung lub-dub
        out = np.zeros(int(SR * 0.9))
        for o, a in ((0.0, 1.0), (0.22, 0.7)):
            x = t(0.22); f = 60 * np.exp(-x * 6) + 38
            w = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(x), 0.004, 0.06) * a
            k = int(o * SR); out[k:k + len(w)] += w
        return out * 1.3
    if jenis == "hentak":  # dentuman kejutan + desis
        x = t(2.2); f = 70 * np.exp(-x * 2) + 32
        b = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 1.6)
        n = _lp(_noise(len(x), seed), 0.25) * np.exp(-x * 5) * 0.7
        return (b + n) * 1.2
    if jenis == "angin":  # hembusan angin malam
        x = t(3.5); n = _noise(len(x), seed); a = 0.01 + 0.05 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.35 * x))
        y = np.empty_like(n); v = 0.0
        for i in range(len(n)):
            v += a[i] * (n[i] - v); y[i] = v
        return y * np.sin(np.pi * np.linspace(0, 1, len(x))) * 4
    return np.zeros(int(SR * 0.05))


def campur(events, durasi, path_wav):
    n = int(SR * (durasi + 1.0)); mix = np.zeros(n); cache = {}
    for i, (t0, jenis, vol) in enumerate(events):
        k = (jenis, i % 5)
        if k not in cache:
            cache[k] = buat(jenis, seed=i % 5 + 1)
        w = cache[k] * vol; o = int(t0 * SR)
        if 0 <= o < n:
            m = min(len(w), n - o); mix[o:o + m] += w[:m]
    pk = np.max(np.abs(mix)) or 1.0
    if pk > 0.85:
        mix *= 0.85 / pk
    mix = np.tanh(mix * 1.1) * 0.9
    with wave.open(path_wav, "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((mix * 32767).astype(np.int16).tobytes())
    return path_wav
