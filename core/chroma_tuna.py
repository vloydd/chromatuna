# core/chroma_tuna.py

import threading
import customtkinter as ctk

from core.chromatuna_engine import TunerEngine
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

    def chromatic_tuning(self):
        print("Chromatic Tuner...")
        x, y = self.app.master.winfo_x(), self.app.master.winfo_y()
        self.top = TunerWindow(self.app.master, "Select Tuning", "+%d+%d" % (x + 50, y + 50))
        self.top.geometry("400x300")
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
            self.top.destroy()

        stop_button = ctk.CTkButton(
            self.top,
            text="Stop & Close",
            command=stop_chromatic,
            fg_color="#DE0A26",
            hover_color="#DC143C",
            font=("Courier New", 14)
        )
        start_button.pack(padx=5, pady=5)
        stop_button.pack(padx=5, pady=5)
