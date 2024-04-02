# core/chromatuna_engine.py

import numpy as np
import sounddevice as sd
import scipy.fftpack
import time
import copy

# importing variables from __init__.py
from core import SAMPLE_FREQ, WINDOW_SIZE, NUM_HPS, CONCERT_PITCH, WHITE_NOISE_THRESH, \
    DELTA_FREQ, OCTAVE_BANDS, ALL_NOTES


class TunerEngine:

    def __init__(self, sample_freq, window_size, window_step, num_hps, power_thresh, white_noise_thresh, app):
        self.sample_freq = sample_freq
        self.window_size = window_size
        self.window_step = window_step
        self.num_hps = num_hps
        self.power_thresh = power_thresh
        self.white_noise_thresh = white_noise_thresh
        self.window_samples = [0 for _ in range(window_size)]
        self.note_buffer = ["1", "2"]
        self.running = False
        self.hann_window = np.hanning(self.window_size)
        self.app = app

    def find_closest_note(self, pitch):
        i = int(np.round(np.log2(pitch / CONCERT_PITCH) * 12))
        closest_note = ALL_NOTES[i % 12] + str(4 + (i + 9) // 12)
        closest_pitch = CONCERT_PITCH * 2 ** (i / 12)
        return closest_note, closest_pitch

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print(status)
            return
        if any(indata):
            self.window_samples = np.concatenate((self.window_samples, indata[:, 0]))
            self.window_samples = self.window_samples[len(indata[:, 0]):]

            signal_power = (np.linalg.norm(self.window_samples, ord=2) ** 2) / len(self.window_samples)
            if signal_power < self.power_thresh:
                print(f"Signal is too weak, check your connection: {signal_power} . Need at least {self.power_thresh}")
                return

            hann_samples = self.window_samples * self.hann_window
            magnitude_spec = abs(scipy.fftpack.fft(hann_samples)[:len(hann_samples) // 2])

            for i in range(int(16 / DELTA_FREQ)):
                magnitude_spec[i] = 0

            for j in range(len(OCTAVE_BANDS) - 1):
                ind_start = int(OCTAVE_BANDS[j] / DELTA_FREQ)
                ind_end = int(OCTAVE_BANDS[j + 1] / DELTA_FREQ)
                ind_end = ind_end if len(magnitude_spec) > ind_end else len(magnitude_spec)
                avg_energy_per_freq = (np.linalg.norm(magnitude_spec[ind_start:ind_end], ord=2) ** 2) / (
                        ind_end - ind_start)
                avg_energy_per_freq = avg_energy_per_freq ** 0.5
                for i in range(ind_start, ind_end):
                    magnitude_spec[i] = magnitude_spec[i] if magnitude_spec[
                                                                 i] > WHITE_NOISE_THRESH * avg_energy_per_freq else 0

            mag_spec_ipol = np.interp(np.arange(0, len(magnitude_spec), 1 / NUM_HPS),
                                      np.arange(0, len(magnitude_spec)),
                                      magnitude_spec)
            mag_spec_ipol = mag_spec_ipol / np.linalg.norm(mag_spec_ipol, ord=2)

            hps_spec = copy.deepcopy(mag_spec_ipol)

            for i in range(NUM_HPS):
                tmp_hps_spec = np.multiply(hps_spec[:int(np.ceil(len(mag_spec_ipol) / (i + 1)))],
                                           mag_spec_ipol[::(i + 1)])
                if not any(tmp_hps_spec):
                    break
                hps_spec = tmp_hps_spec

            max_ind = np.argmax(hps_spec)
            max_freq = max_ind * (SAMPLE_FREQ / WINDOW_SIZE) / NUM_HPS

            closest_note, closest_pitch = self.find_closest_note(max_freq)
            max_freq = round(max_freq, 1)
            closest_pitch = round(closest_pitch, 1)

            self.note_buffer.insert(0, closest_note)
            self.note_buffer.pop()

            if self.note_buffer.count(self.note_buffer[0]) == len(self.note_buffer):
                print(f"Closest note: {closest_note} {max_freq}/{closest_pitch}: {signal_power}")
            self.update_gui(closest_note, max_freq, closest_pitch, (max_freq - closest_pitch))

    def update_gui(self, note, freq, pitch, diff):
        pass

    def start_stream(self):
        self.running = True
        print("Starting tuner...")
        try:
            with sd.InputStream(channels=1, callback=self.audio_callback, blocksize=self.window_step,
                                samplerate=self.sample_freq):
                while self.running:
                    time.sleep(0.3)
        except Exception as exc:
            print(str(exc))

    def stop_stream(self):
        self.running = False
        self.update_gui('-', '0.00', '0.00', 0)
        print("Stopping tuner...")
