# main.py

from gui.tuner_app import TunerApp
import customtkinter as ctk

if __name__ == "__main__":
    root = ctk.CTk()
    app = TunerApp(root)
    root.mainloop()
