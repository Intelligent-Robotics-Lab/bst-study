import random
import librosa
import soundfile as sf

y, sr = librosa.load("base.wav")

# Raise pitch
y = librosa.effects.pitch_shift(
    y,
    sr=sr,
    n_steps=random.uniform(4, 8)
)

# Slightly speed up
y = librosa.effects.time_stretch(
    y,
    rate=random.uniform(1.1, 1.4)
)

sf.write("scream.wav", y, sr)