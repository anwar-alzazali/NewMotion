"""Musik latar sintetis bebas royalti (numpy, tanpa berkas luar).
buat(gaya, durasi, path_wav, seed): gaya = santai (lo-fi), semangat (pop ceria), tenang (pad lembut), teknologi (synth pulse), mencekam (misteri, tanpa drum).
Dicampur di papan_buat.py dengan ducking (volume turun saat narasi bicara)."""
import wave
import numpy as np

SR = 44100

GAYA = {
    # bpm, progresi akor (semitone dari C4), pola bass, ada drum, kecerahan
    "santai":    dict(bpm=84,  akor=[[0, 4, 7, 11], [-3, 0, 4, 7], [-7, -3, 0, 4], [-5, -1, 2, 5]], drum="lofi", terang=0.35, arp=True),
    "semangat":  dict(bpm=112, akor=[[0, 4, 7, 12], [-5, -1, 2, 7], [-3, 0, 4, 9], [-7, -3, 0, 5]], drum="pop", terang=0.6, arp=True),
    "tenang":    dict(bpm=70,  akor=[[0, 4, 7, 14], [-3, 0, 7, 9], [-7, 0, 4, 9], [-5, 2, 5, 11]], drum=None, terang=0.25, arp=False),
    "teknologi": dict(bpm=100, akor=[[-3, 0, 4, 7], [-7, -3, 0, 5], [-5, -1, 2, 7], [-8, -5, -1, 4]], drum="tek", terang=0.5, arp=True),
}


def _hz(semi, oktaf=0):
    return 261.63 * 2 ** ((semi + 12 * oktaf) / 12)


def _lp(x, a):
    # lowpass satu kutub (vektor lewat filter rekursif sederhana per blok)
    y = np.empty_like(x); s = 0.0
    for i in range(len(x)):
        s += a * (x[i] - s); y[i] = s
    return y


def _env(n, atk, rel):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(atk, 1e-4))
    sisa = n / SR - t
    return e * np.minimum(1, sisa / max(rel, 1e-4))


def _pad(frek, n, terang, rng):
    t = np.arange(n) / SR
    x = np.zeros(n)
    for f in frek:
        for det in (-0.12, 0.0, 0.11):  # chorus ringan
            ff = f * 2 ** (det / 12)
            x += np.sin(2 * np.pi * ff * t + rng.uniform(0, 6.28)) * 0.55
            x += np.sin(2 * np.pi * 2 * ff * t) * 0.18 * terang
    return x / (len(frek) * 3) * _env(n, 0.35, 0.4)


def _pluck(f, dur, terang):
    n = int(SR * dur); t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f * t) + 0.35 * terang * np.sin(2 * np.pi * 2 * f * t) + 0.12 * np.sin(2 * np.pi * 3 * f * t))
    return x * np.exp(-t * 7) * np.minimum(1, t / 0.004)


def _kick(n0=0.35):
    n = int(SR * n0); t = np.arange(n) / SR
    f = 50 + 90 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def _snare(rng, d=0.18):
    n = int(SR * d); t = np.arange(n) / SR
    no = rng.uniform(-1, 1, n)
    return (no - _lp(no, 0.08)) * np.exp(-t * 22) * 0.6 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * 0.3


def _hat(rng, d=0.05):
    n = int(SR * d); no = rng.uniform(-1, 1, n)
    return (no - _lp(no, 0.3)) * np.exp(-np.arange(n) / SR * 70) * 0.35


def _mencekam(durasi, rng):
    """Dengung minor gelap tanpa drum: pad rendah, nada sumbang yang membengkak, denyut pelan."""
    n = int(SR * (durasi + 1.0)); x = np.arange(n) / SR; mix = np.zeros(n)
    akor = [[-12, -9, -5], [-16, -12, -9], [-14, -10, -7], [-13, -9, -6]]  # Am, F, Dm, E (tegang)
    blok = 6.0
    for b in range(int(np.ceil((durasi + 1) / blok))):
        o = int(b * blok * SR); m = min(int(blok * 1.15 * SR), n - o)
        if m <= 0: break
        tt = np.arange(m) / SR; env = np.minimum(1, tt / 1.5) * np.minimum(1, (blok * 1.15 - tt) / 1.5)
        for s in akor[b % 4]:
            f = _hz(s, -1)
            mix[o:o + m] += (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 1.003 * tt)) * env * 0.22
    mix += np.sin(2 * np.pi * 41.2 * x) * 0.25 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * x))      # dengung dasar
    nada = 0.06 * np.sin(2 * np.pi * _hz(6, 1) * x) * np.clip(np.sin(2 * np.pi * x / 11.0), 0, 1) ** 3  # nada sumbang tinggi
    mix += nada
    for k in np.arange(2.0, durasi, 4.0):  # denyut pelan
        o = int(k * SR); w = _kick(0.5) * 0.35; m = min(len(w), n - o)
        if m > 0: mix[o:o + m] += w[:m]
    return mix


def buat(gaya, durasi, path_wav, seed=3):
    if gaya == "mencekam":
        rng = np.random.default_rng(seed); n = int(SR * (durasi + 1.0)); mix = _mencekam(durasi, rng)
        f_in = np.minimum(1, np.arange(n) / (SR * 2.0)); f_out = np.clip((durasi + 0.8 - np.arange(n) / SR) / 2.0, 0, 1)
        mix *= f_in * f_out; pk = np.max(np.abs(mix)) or 1.0; mix = np.tanh(mix / pk * 1.1) * 0.8
        st = np.stack([mix, np.roll(mix, int(SR * 0.018))], axis=1)
        with wave.open(path_wav, "wb") as f:
            f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR); f.writeframes((st * 32767).astype(np.int16).tobytes())
        return path_wav
    g = GAYA.get(gaya, GAYA["santai"])
    rng = np.random.default_rng(seed)
    ketuk = 60 / g["bpm"]; birama = ketuk * 4
    n = int(SR * (durasi + 1.0)); mix = np.zeros(n)

    def taruh(w, t0, vol):
        o = int(t0 * SR)
        if o >= n:
            return
        m = min(len(w), n - o); mix[o:o + m] += w[:m] * vol

    jumlah = int(np.ceil((durasi + 1) / birama))
    kick, snare, hat = _kick(), _snare(rng), _hat(rng)
    for b in range(jumlah):
        t0 = b * birama; ak = g["akor"][b % len(g["akor"])]
        taruh(_pad([_hz(s) for s in ak], int(SR * birama * 1.02), g["terang"], rng), t0, 0.55)
        taruh(_pluck(_hz(ak[0], -2), birama * 0.9, 0.3), t0, 0.5)                         # bass
        taruh(_pluck(_hz(ak[0] + (7 if b % 2 else 0), -2), ketuk * 1.5, 0.3), t0 + ketuk * 2.5, 0.3)
        if g["arp"]:
            pola = [ak[0], ak[2], ak[1], ak[3], ak[2], ak[1], ak[3], ak[2]]
            for i, s in enumerate(pola):
                if rng.random() < 0.85:
                    taruh(_pluck(_hz(s, 1), ketuk * 0.6, g["terang"]), t0 + i * ketuk / 2, 0.16)
        if g["drum"]:
            for k in range(4):
                tk = t0 + k * ketuk
                if k in (0, 2) or (g["drum"] == "pop" and k == 3 and b % 2):
                    taruh(kick, tk, 0.55 if g["drum"] != "lofi" else 0.45)
                if k in (1, 3):
                    taruh(snare, tk + (0.02 if g["drum"] == "lofi" else 0), 0.35)
                for h in range(2):
                    taruh(hat, tk + h * ketuk / 2 + (0.03 if h and g["drum"] == "lofi" else 0), 0.25 if h else 0.18)
    if g["drum"] == "lofi":  # sedikit kresek piringan hitam
        cr = rng.uniform(-1, 1, n) * (rng.random(n) < 0.0008) * 0.25
        mix += cr
    # masuk dan keluar lembut
    f_in = np.minimum(1, np.arange(n) / (SR * 1.2))
    f_out = np.clip((durasi + 0.8 - np.arange(n) / SR) / 2.0, 0, 1)
    mix *= f_in * f_out
    pk = np.max(np.abs(mix)) or 1.0
    mix = np.tanh(mix / pk * 1.2) * 0.8
    st = np.stack([mix, np.roll(mix, int(SR * 0.012))], axis=1)  # stereo lebar sedikit
    with wave.open(path_wav, "wb") as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((st * 32767).astype(np.int16).tobytes())
    return path_wav


if __name__ == "__main__":
    import sys
    buat(sys.argv[1] if len(sys.argv) > 1 else "santai", float(sys.argv[2]) if len(sys.argv) > 2 else 20, sys.argv[3] if len(sys.argv) > 3 else "/tmp/musik.wav")
