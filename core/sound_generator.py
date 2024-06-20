# core/sound_generator.py

import numpy as np


class SoundGenerator:
    def generate_sound(self, instrument='guitar', frequency=55, duration=2.5, sample_rate=44100):
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        num_samples = len(t)

        # define the amplitudes for the fundamental and harmonics
        fundamental_amp = 0.8

        if instrument == 'violin':
            harmonic_amps = [0.6, 0.4, 0.3, 0.2, 0.1, 0.1, 0.1, 0.05, 0.05]
            attack_duration = 1  # attack -  1 sec
            decay_duration = 0.2  # decay(falling) - 200 ms
            sustain_level = 0.8
            release_duration = 1  # release - 100ms
        elif instrument == 'guitar':
            harmonic_amps = [0.8, 0.4, 0.2, 0.1, 0.05]
            attack_duration = 0.1
            decay_duration = 0.3
            sustain_level = 0.5
            release_duration = 0.4
        elif instrument == 'ukulele':
            harmonic_amps = [0.7, 0.3, 0.1, 0.05]
            attack_duration = 0.05
            decay_duration = 0.15
            sustain_level = 0.6
            release_duration = 0.2
        else:
            harmonic_amps = [0.6, 0.4, 0.3, 0.2, 0.1]
            attack_duration = 0.02  # 20 ms
            decay_duration = 1.2  # decay(falling) - 1200 ms
            sustain_level = 0.6
            release_duration = 0.7  # release - 700ms


        # generate the fundamental sine wave
        fundamental = fundamental_amp * np.sin(2 * np.pi * frequency * t)

        # generate the harmonics
        harmonics = np.zeros_like(fundamental)
        for i, amp in enumerate(harmonic_amps, start=2):
            harmonic_freq = frequency * i
            harmonics += amp * np.sin(2 * np.pi * harmonic_freq * t)

        # combine the fundamental and harmonics
        sound_tone = fundamental + harmonics

        # apply a container to shape the tone
        attack_env = np.linspace(0, 1, int(attack_duration * sample_rate))
        decay_env = np.linspace(1, sustain_level, int(decay_duration * sample_rate))
        sustain_env = np.full(num_samples - len(attack_env) - len(decay_env) - int(release_duration * sample_rate),
                              sustain_level)
        release_env = np.linspace(sustain_level, 0, int(release_duration * sample_rate))

        envelope = np.concatenate((attack_env, decay_env, sustain_env, release_env))

        # ensure the envelope length matches the sound tone length
        envelope = np.resize(envelope, num_samples)
        sound_tone *= envelope
        return sound_tone
