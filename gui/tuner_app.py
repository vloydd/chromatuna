# gui/tuner_app.py

import json
import tkinter as tk
from tkinter import END
import customtkinter as ctk
import sounddevice as sd
import soundfile as sf

from core.sound_generator import SoundGenerator
from core.chromatuna_engine import TunerEngine
from gui.tuner_window import TunerWindow
from core.chroma_tuna import ChromaTuna
from core import SAMPLE_FREQ, WINDOW_SIZE, WINDOW_STEP, NUM_HPS, POWER_THRESH, WHITE_NOISE_THRESH


class TunerApp:
    def __init__(self, master):
        self.tunings = None
        self.tuning = None
        self.instrument = None
        self.master = master
        self.tuner_engine = TunerEngine(
            SAMPLE_FREQ,
            WINDOW_SIZE,
            WINDOW_STEP,
            NUM_HPS,
            POWER_THRESH,
            WHITE_NOISE_THRESH,
            self
        )
        self.chromatic_tuner = ChromaTuna(self.tuner_engine)
        self.sound_generator = SoundGenerator()
        self.default_configuration()
        self.setup_gui()

    def default_configuration(self):
        # get instrument & its tunings from json file
        with open("assets/tunings.json", "r") as file:
            self.tunings = json.load(file)
        self.instrument = 'guitar'
        self.tuning = 'standard'

    def setup_gui(self):
        self.master.title("Chromatuna")
        self.master.geometry("550x500")
        self.master.resizable(False, False)
        self.master.iconbitmap("assets/chromatuna.ico")
        # self.master.wm_attributes('-toolwindow', 'True')

        instrument_list = tk.Listbox(
            self.master,
            font=("Cascadia Mono", 12),
            bg="#66B66E",
            selectmode=tk.SINGLE
        )

        instrument_list.pack(expand=False, padx=5, pady=5)
        instrument_list.bind('<<ListboxSelect>>', self.instrument_selected)

        for name in self.tunings:
            instrument_list.insert(END, name.capitalize())
        instrument_list.selection_set(list(self.tunings).index(self.instrument))

        tuning_button = ctk.CTkButton(
            self.master,
            text="Choose Tuning",
            command=self.select_tuning,
            width=150,
            height=40,
            fg_color="transparent",
            hover_color="#FF5B00",
            border_width=1,
            border_color="#FF5B00",
            corner_radius=20,
            font=("Cascadia Mono", 11),
        )
        start_tuning = ctk.CTkButton(
            self.master,
            text="Start Tuning",
            command=self.chromatic_tuner.full_tuning,
            width=150,
            height=40,
            fg_color="transparent",
            hover_color="#66B66E",
            border_width=1,
            border_color="#66B66E",
            corner_radius=50,
            font=("Cascadia Mono", 14),
        )
        chromatic_button = ctk.CTkButton(
            self.master,
            text="Chromatic Only",
            command=self.chromatic_tuner.chromatic_tuning,
            width=150,
            height=40,
            fg_color="transparent",
            hover_color="#FFA500",
            border_width=1,
            corner_radius=50,
            border_color="#FFA500",
            font=("Cascadia Mono", 14),
        )

        instrument_list.pack(expand=True, padx=5, pady=5)
        tuning_button.pack(padx=10, pady=10)
        start_tuning.pack(padx=10, pady=10)
        chromatic_button.pack(padx=10, pady=10)

    def select_tuning(self):
        print("Selecting tuning...")
        x, y = self.master.winfo_x(), self.master.winfo_y()
        top = TunerWindow(self.master, "Selecting tuning", "+%d+%d" % (x + 135, y + 75))
        top.geometry("350x300")
        top.overrideredirect(True)
        top.config(bg="#242424", bd=5, relief=tk.RAISED, border=5)
        tunings = self.tunings[self.instrument]
        listbox = tk.Listbox(top, bg="#66B", font=("Cascadia Mono", 12), selectmode=tk.SINGLE)
        if tunings:
            for tuning in tunings.keys():
                # insert tuning names into the listbox
                listbox.insert(END, tunings[tuning][0]['name'])
        listbox.selection_set(list(self.tunings[self.instrument]).index(self.tuning))

        def on_selection(event):
            # wrapper function to handle select and window close
            self.get_tuning_selection(event)
            top.destroy()

        listbox.bind("<<ListboxSelect>>", on_selection)
        listbox.pack(padx=5, pady=5)

    def get_tuning_selection(self, event):
        widget = event.widget
        index = int(widget.curselection()[0])
        self.tuning = list(self.tunings[self.instrument].keys())[index]  # update the current tuning preset
        print(f"Tuning selected: {self.tuning}")

    def instrument_selected(self, event):
        widget = event.widget
        selections = widget.curselection()
        selected_items = [widget.get(i) for i in selections]
        # check if instrument is selected
        if selected_items is not None and len(selected_items) > 0:
            selected_item = selected_items.pop()
            self.instrument = selected_item.lower()
            self.tuning = 'standard'
            print("Selected instrument: " + selected_item)

    def get_tuning_frequencies(self):
        return list(self.tunings[self.instrument][self.tuning][0]['tuning'].values())

    def get_tuning_keys(self):
        list(self.tunings[self.instrument][self.tuning][0]['tuning'].keys())