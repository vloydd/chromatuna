# gui/string_tuner_window.py
import threading

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sounddevice as sd
import soundfile as sf

from core.sound_generator import SoundGenerator


class StringTunerWindow(ctk.CTkToplevel):
    def __init__(self, master, app, instrument, tuning, string_order, target_freq, tuner_engine, chromatic_tuner):
        super().__init__(master)
        self.sound_generator = SoundGenerator()
        self.title(f"Tuning {instrument.capitalize()} - {tuning.capitalize()}")
        self.geometry("600x1200")
        self.app = app
        self.instrument = instrument
        self.tuning = tuning
        self.string_order = string_order
        self.current_string_index = 0
        self.target_freq = target_freq
        self.tuner_engine = tuner_engine
        self.chromatic_tuner = chromatic_tuner

        self.current_string_label = ctk.CTkLabel(
            self,
            text=f"Current String: {self.string_order[self.current_string_index]}",
            font=("Verdana", 14))
        self.current_string_label.pack(padx=10, pady=10)

        self.target_freq_label = ctk.CTkLabel(
            self,
            text=f"Target Frequency: {self.target_freq} Hz",
            font=("Verdana", 14))
        self.target_freq_label.pack(padx=10, pady=10)

        self.play_pitch = ctk.CTkButton(
            self,
            text="Play Sound",
            command=self.play_sound,
            width=150,
            height=40,
            fg_color="transparent",
            hover_color="#FFA500",
            border_width=1,
            corner_radius=50,
            border_color="#FFA500",
            font=("Cascadia Mono", 14),
        )

        # Add other GUI elements here (e.g., signal and FFT visualizations)
        self.play_pitch.pack(padx=10, pady=10)
        self.next_button = ctk.CTkButton(
            self,
            text="Next String",
            command=self.next_string,
            font=("Courier New", 14)
        )
        self.next_button.pack(padx=10, pady=10)

        start_button = ctk.CTkButton(
            self,
            text="Start",
            command=self.start_tuning,
            fg_color="#66B66E",
            hover_color="#6FC276",
            font=("Courier New", 14)
        )

        def stop_tuning():
            self.tuner_engine.stop_stream()
        # def stop_chromatic():
        #     self.stop_tuning()
            # self.top.destroy()

        stop_button = ctk.CTkButton(
            self,
            text="Stop",
            command=stop_tuning,
            fg_color="#DE0A26",
            hover_color="#DC143C",
            font=("Verdana", 14)
        )
        start_button.pack(padx=5, pady=5)
        stop_button.pack(padx=5, pady=5)

    def next_string(self):
        self.current_string_index += 1
        if self.current_string_index < len(self.string_order):
            next_string = self.string_order[self.current_string_index]
            next_target_freq = self.app.tunings[self.instrument][self.tuning][0]['tuning'][next_string]
            self.current_string_label.configure(text=f"Current String: {next_string}")
            self.target_freq_label.configure(text=f"Target Frequency: {next_target_freq} Hz")
            self.target_freq = next_target_freq
        else:
            self.destroy()

    def update_gui(self, note, freq, pitch, diff=0):
        current_freq = round(freq, 1)
        diff = round(diff, 1)
        if diff > 0:
            diff_text = f"+{diff}"
        elif diff < 0:
            diff_text = f"{diff}"
        else:
            diff_text = ""

        self.current_string_label.configure(text=f"Current String: {self.string_order[self.current_string_index]}")
        self.target_freq_label.configure(text=f"Target Frequency: {self.target_freq} Hz")
        self.diff_label.configure(text=f"Difference: {diff_text} Hz")

        if abs(diff) <= 1:
            self.next_string()

        self.chromatic_tuner.update_gui(note, freq, pitch, diff)

    def play_sound(self):
        guitar_sound = self.sound_generator.generate_sound(self.instrument, self.target_freq)
        sd.play(guitar_sound, blocking=False)
        # Save the generated guitar tone to a WAV file
        wav_file_path = 'assets/' + self.instrument + '/' + self.string_order[self.current_string_index] + '_' + str(self.target_freq) + '.wav'
        sf.write(wav_file_path, guitar_sound, 44100)

    def start_tuning(self):
        if self.tuner_engine.stream_thread is None or not self.tuner_engine.stream_thread.is_alive():
            self.tuner_engine.stream_thread = threading.Thread(target=self.tuner_engine.start_stream)
            self.tuner_engine.stream_thread.start()