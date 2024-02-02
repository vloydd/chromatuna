import numpy as np
import sounddevice as sd
import scipy.fftpack
import threading
import time
import copy
import customtkinter as ctk

# General settings
SAMPLE_FREQ = 48000  # sample frequency in Hz
WINDOW_SIZE = 48000  # window size of the DFT in samples
WINDOW_STEP = 12000  # step size of window
NUM_HPS = 5  # max number of harmonic product spectrums
POWER_THRESH = 1e-5  # tuning is activated if the signal power exceeds this threshold
CONCERT_PITCH = 440  # defining a1
WHITE_NOISE_THRESH = 0.2  # everything under WHITE_NOISE_THRESH*avg_energy_per_freq is cut off

WINDOW_T_LEN = WINDOW_SIZE / SAMPLE_FREQ  # length of the window in seconds
SAMPLE_T_LENGTH = 1 / SAMPLE_FREQ  # length between two samples in seconds
DELTA_FREQ = SAMPLE_FREQ / WINDOW_SIZE  # frequency step width of the interpolated DFT
OCTAVE_BANDS = [50, 100, 200, 400, 800, 1600, 3200, 6400, 12800, 25600]  # octave bands for the frequency calculation


class Tuner:
    # there are 12 notes in an octave.
    ALL_NOTES = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]
    # base frequency of the a4 note - 440Hz
    CONCERT_PITCH = 440

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
        # find i via log2 - difference in semitones between the pitch and the concert pitch
        i = int(np.round(np.log2(pitch / self.CONCERT_PITCH) * 12))
        # find the closest note to the pitch and its octave based on steps
        closest_note = self.ALL_NOTES[i % 12] + str(4 + (i + 9) // 12)
        # find f(i) - the closest pitch to the freq
        closest_pitch = self.CONCERT_PITCH * 2 ** (i / 12)
        return closest_note, closest_pitch

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print(status)
            return
        if any(indata):
            self.window_samples = np.concatenate((self.window_samples, indata[:, 0]))
            self.window_samples = self.window_samples[len(indata[:, 0]):]

            # skip if signal power is too low
            signal_power = (np.linalg.norm(self.window_samples, ord=2) ** 2) / len(self.window_samples)
            if signal_power < self.power_thresh:
                print(f"Signal is too weak, check your connection: {signal_power} . Need at least {self.power_thresh}")
                return

            # avoid spectral leakage by multiplying the signal with a hann window
            hann_samples = self.window_samples * self.hann_window
            magnitude_spec = abs(scipy.fftpack.fft(hann_samples)[:len(hann_samples) // 2])

            # supress mains hum, set everything below 32Hz to zero - assuming that the lowest note is a C0
            for i in range(int(16 / DELTA_FREQ)):
                magnitude_spec[i] = 0

            # calculate average energy per frequency for the octave bands
            # and suppress everything below it
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

            # interpolate spectrum
            mag_spec_ipol = np.interp(np.arange(0, len(magnitude_spec), 1 / NUM_HPS), np.arange(0, len(magnitude_spec)),
                                      magnitude_spec)
            mag_spec_ipol = mag_spec_ipol / np.linalg.norm(mag_spec_ipol, ord=2)  # normalize it

            hps_spec = copy.deepcopy(mag_spec_ipol)

            # calculate the HPS
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

            self.note_buffer.insert(0, closest_note)  # note that this is a ringbuffer
            self.note_buffer.pop()

            if self.note_buffer.count(self.note_buffer[0]) == len(self.note_buffer):
                print(f"Closest note: {closest_note} {max_freq}/{closest_pitch}: {signal_power}")
            self.update_gui(closest_note, max_freq, closest_pitch, (max_freq - closest_pitch))

    def update_gui(self, note, freq, pitch, diff):
        self.app.update_gui(note, freq, pitch, diff)

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


class TunerApp:
    def __init__(self, master):
        self.master = master
        self.tuner = Tuner(SAMPLE_FREQ, WINDOW_SIZE, WINDOW_STEP, NUM_HPS, POWER_THRESH, WHITE_NOISE_THRESH, self)
        self.setup_gui()
        self.stream_thread = None

    def setup_gui(self):
        self.master.title("Chromatuna")
        self.master.geometry("500x200")
        self.master.resizable(False, False)

        self.closest_note_var = ctk.StringVar(value="Closest Note: -")
        self.freq_var = ctk.StringVar(value="Your Freq: 0.0")
        self.pitch_var = ctk.StringVar(value="Target Pitch: 0.0")
        self.diff_var = ctk.StringVar(value="Difference: 0")
        closest_note_label = ctk.CTkLabel(self.master, textvariable=self.closest_note_var, font=("Verdana", 14))
        freq_label = ctk.CTkLabel(self.master, textvariable=self.freq_var, font=("Verdana", 14))
        pitch_label = ctk.CTkLabel(self.master, textvariable=self.pitch_var, font=("Verdana", 14))
        diff_label = ctk.CTkLabel(self.master, textvariable=self.diff_var, font=("Verdana", 14))
        closest_note_label.pack()
        freq_label.pack()
        pitch_label.pack()
        diff_label.pack()

        start_button = ctk.CTkButton(
            self.master,
            text="Start",
            command=self.start_tuning,
            fg_color="#66B66E",
            hover_color="#6FC276",
            font=("Courier New", 14)
        )
        stop_button = ctk.CTkButton(
            self.master,
            text="Stop",
            command=self.stop_tuning,
            fg_color="#DE0A26",
            hover_color="#DC143C",
            font=("Courier New", 14)
        )
        start_button.pack(padx=5, pady=5)
        stop_button.pack(padx=5, pady=5)

    def start_tuning(self):
        if self.stream_thread is None or not self.stream_thread.is_alive():
            self.stream_thread = threading.Thread(target=self.tuner.start_stream)
            self.stream_thread.start()

    def update_gui(self, note, freq, pitch, diff=0):
        self.closest_note_var.set(f"Closest Note: {note}")
        self.freq_var.set(f"Your Freq: {freq}")
        self.pitch_var.set(f"Target Pitch: {pitch}")
        if diff != 0:
            diff = int(diff * 10)
            if diff > 0:
                diff = f"+{diff}"
            self.diff_var.set(f"Difference: {diff}")
        else:
            self.diff_var.set('')

    def stop_tuning(self):
        self.tuner.stop_stream()


if __name__ == "__main__":
    root = ctk.CTk()
    app = TunerApp(root)
    root.mainloop()
