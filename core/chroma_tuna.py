# core/chroma_tuna.py

import threading
import customtkinter as ctk
import numpy as np
import matplotlib.pyplot as plt

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from core.chromatuna_engine import TunerEngine
from core.string_tuner_window import StringTunerWindow
from gui.tuner_window import TunerWindow


class ChromaTuna(TunerEngine):
    def __init__(self, tuner_engine):
        super().__init__(
            tuner_engine.sample_freq,
            tuner_engine.window_size,
            tuner_engine.window_step,
            tuner_engine.num_hps,
            tuner_engine.power_thresh,
            tuner_engine.white_noise_thresh,
            tuner_engine.app
        )
        self.top = None
        self.stream_thread = None
        self.closest_note_var = None
        self.freq_var = None
        self.pitch_var = None
        self.diff_var = None
        self.closest_note_label = None
        self.freq_label = None
        self.pitch_label = None
        self.diff_label = None
        self.fig_signal, self.ax_signal = plt.subplots(figsize=(4, 3))
        self.fig_fft, self.ax_fft = plt.subplots(figsize=(4, 3))
        self.signal_canvas = None
        self.fft_canvas = None
        self.fft_data = None
        self.fft_freqs = None

    def start_tuning(self):
        if self.stream_thread is None or not self.stream_thread.is_alive():
            self.stream_thread = threading.Thread(target=self.start_stream)
            self.stream_thread.start()

    def stop_tuning(self):
        self.stop_stream()

    def update_gui(self, note, freq, pitch, diff=0):
        if self.running is False:
            return
        if self.closest_note_label:
            self.closest_note_label.configure(text=f"Closest Note: {note}")
        if self.freq_label:
            self.freq_label.configure(text=f"Freq: {freq}")
        if self.pitch_label:
            self.pitch_label.configure(text=f"Target Pitch: {pitch}")
        if self.diff_label:
            if diff != 0:
                diff = int(diff * 10)
                if diff > 0:
                    diff = f"+{diff}"
                self.diff_label.configure(text=f"Difference: {diff}")
            else:
                self.diff_label.configure(text='')

        if self.signal_canvas is None:
            self.signal_canvas = FigureCanvasTkAgg(self.fig_signal, self.top)
            self.signal_canvas.draw()
            self.signal_canvas.get_tk_widget().pack(padx=5, pady=5)
        self.ax_signal.clear()
        self.ax_signal.plot(np.abs(self.window_samples))
        self.ax_signal.set_title("Amplitude")
        self.signal_canvas.draw()

        if self.fft_canvas is None:
            self.fft_canvas = FigureCanvasTkAgg(self.fig_fft, self.top)
            self.fft_canvas.draw()
            self.fft_canvas.get_tk_widget().pack(padx=50, pady=50)

        self.ax_fft.clear()
        nyquist_freq = self.sample_freq / 2
        max_freq = 700  # set 700 as the max frequency - crop rest of the data.

        # crop the FFT data to the max frequency.
        start_idx = 0
        end_idx = int(max_freq / (nyquist_freq / len(self.fft_freqs)))

        self.ax_fft.semilogy(self.fft_freqs[start_idx:end_idx], self.fft_data[start_idx:end_idx])
        self.ax_fft.set_xlim(0, max_freq)
        self.ax_fft.set_title("FFT")
        self.ax_fft.set_xlabel("Frequency (Hz)")
        self.ax_fft.set_ylabel("Amplitude")
        self.fft_canvas.draw()

    def chromatic_tuning(self):
        print("Chromatic Tuner...")
        x, y = self.app.master.winfo_x(), self.app.master.winfo_y()
        self.top = TunerWindow(self.app.master, "ChromaTuna", "+%d+%d" % (x + 50, y + 50))
        # self.top.geometry("400x300")
        self.top.geometry("600x1400")
        self.closest_note_label = ctk.CTkLabel(self.top, text="Closest Note: -", font=("Verdana", 14))
        self.freq_label = ctk.CTkLabel(self.top, text="Freq: -", font=("Verdana", 14))
        self.pitch_label = ctk.CTkLabel(self.top, text="Target Pitch: -", font=("Verdana", 14))
        self.diff_label = ctk.CTkLabel(self.top, text="Difference: -", font=("Verdana", 14))

        self.closest_note_label.pack()
        self.freq_label.pack()
        self.pitch_label.pack()
        self.diff_label.pack()

        start_button = ctk.CTkButton(
            self.top,
            text="Start",
            command=self.start_tuning,
            fg_color="#66B66E",
            hover_color="#6FC276",
            font=("Courier New", 14)
        )

        def stop_chromatic():
            self.stop_tuning()
            # self.top.destroy()

        stop_button = ctk.CTkButton(
            self.top,
            text="Stop",
            command=stop_chromatic,
            fg_color="#DE0A26",
            hover_color="#DC143C",
            font=("Verdana", 14)
        )
        start_button.pack(padx=5, pady=5)
        stop_button.pack(padx=5, pady=5)

    def full_tuning(self):
        tuning_data = self.app.tunings[self.app.instrument][self.app.tuning][0]
        string_order = list(tuning_data['tuning'].keys())
        target_freq = list(tuning_data['tuning'].values())[0]

        self.top = StringTunerWindow(
            self.app.master,
            self.app,
            self.app.instrument,
            self.app.tuning,
            string_order,
            target_freq,
            self,
            self.app.tuner_engine
        )
        self.top.grab_set()
