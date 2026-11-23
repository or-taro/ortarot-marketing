"""오르타로 오리지널 배경음(직접 합성, 저작권 걱정 없음). python3 bgm.py out.wav 초 [seed]"""
import numpy as np, sys, wave
out, dur = sys.argv[1], float(sys.argv[2]); seed = int(sys.argv[3]) if len(sys.argv) > 3 else 0
SR = 44100; n = int(SR * dur); t = np.arange(n) / SR; rng = np.random.default_rng(seed)
def hz(m): return 440 * 2 ** ((m - 69) / 12)
progs = [[57, 60, 64, 67], [53, 57, 60, 64], [48, 52, 55, 59], [55, 59, 62, 66]]  # Am7 Fmaj7 Cmaj7 G(add)
rot = seed % 4; progs = progs[rot:] + progs[:rot]
pad = np.zeros(n); seg = dur / 4
for i, ch in enumerate(progs):
    a, b = int(i * seg * SR), int(min(n, (i + 1) * seg * SR + SR))
    tt = t[a:b] - t[a]; env = np.minimum(1, tt / 1.5) * np.minimum(1, (tt[-1] - tt + 1e-3) / 1.5)
    for m in ch:
        f = hz(m); pad[a:b] += env * (np.sin(2*np.pi*f*tt) + 0.3*np.sin(2*np.pi*2*f*tt + 0.5) + 0.15*np.sin(2*np.pi*f*1.003*tt))
bell = np.zeros(n); scale = [69, 72, 76, 79, 81, 84]
step = 0.75
for k in range(int(dur / step)):
    if rng.random() < 0.55:
        s = int(k * step * SR); f = hz(rng.choice(scale)); L = min(n - s, int(2.5 * SR)); tt = np.arange(L) / SR
        bell[s:s+L] += np.exp(-tt * 2.2) * (np.sin(2*np.pi*f*tt) + 0.25*np.sin(2*np.pi*2.76*f*tt) * np.exp(-tt*4))
mix = pad / (np.abs(pad).max() + 1e-9) * 0.55 + bell / (np.abs(bell).max() + 1e-9) * 0.35
for d, g in ((0.29, 0.35), (0.53, 0.25), (0.97, 0.18)):  # 간단한 잔향
    k = int(d * SR); mix[k:] += g * mix[:-k]
fade = np.minimum(1, np.minimum(t / 1.0, (dur - t) / 1.5)); mix *= fade
mix = mix / np.abs(mix).max() * 0.25  # 약 -12dBFS
st = np.stack([mix, np.roll(mix, int(0.012 * SR))], 1)
w = wave.open(out, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes()); w.close()
print("ok", out, dur)
