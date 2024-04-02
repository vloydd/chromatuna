# gui/tuner_window.py

import customtkinter as ctk


class TunerWindow(ctk.CTkToplevel):
    def __init__(self, master, title, geometry):
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.geometry(geometry)
        self.grab_set()
