# core/sound_generator.py

import numpy as np


class SoundGenerator:
    def generate_bass_tone(self, frequency=100, duration=1.0, sample_rate=44100):
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        num_samples = len(t)

        # define the amplitudes for the fundamental and harmonics
        fundamental_amp = 0.8
        harmonic_amps = [0.6, 0.4, 0.3, 0.2, 0.1]

        # generate the fundamental sine wave
        fundamental = fundamental_amp * np.sin(2 * np.pi * frequency * t)

        # generate the harmonics
        harmonics = np.zeros_like(fundamental)
        for i, amp in enumerate(harmonic_amps, start=2):
            harmonic_freq = frequency * i
            harmonics += amp * np.sin(2 * np.pi * harmonic_freq * t)

        # combine the fundamental and harmonics
        guitar_tone = fundamental + harmonics

        # apply an envelope to shape the tone
        attack_duration = 0.02  # 10 ms attack
        decay_duration = 1.2  # 300 ms decay
        sustain_level = 0.4
        release_duration = 0.1  # 100 ms release
        attack_env = np.linspace(0, 1, int(attack_duration * sample_rate))
        decay_env = np.linspace(1, sustain_level, int(decay_duration * sample_rate))
        sustain_env = np.full(num_samples - len(attack_env) - len(decay_env) - int(release_duration * sample_rate),
                              sustain_level)
        release_env = np.linspace(sustain_level, 0, int(release_duration * sample_rate))

        envelope = np.concatenate((attack_env, decay_env, sustain_env, release_env))

        # ensure the envelope length matches the guitar_tone length
        envelope = np.resize(envelope, num_samples)
        guitar_tone *= envelope
        return guitar_tone
