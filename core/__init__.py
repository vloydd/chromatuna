# General settings
SAMPLE_FREQ = 48000  # sample frequency in Hz
WINDOW_SIZE = 48000  # window size of the DFT in samples
WINDOW_STEP = 12000  # step size of window
NUM_HPS = 5  # max number of harmonic product spectrums
POWER_THRESH = 1e-5  # tuning is activated if the signal power exceeds this threshold
CONCERT_PITCH = 440  # base frequency of the a4 note - 440Hz
WHITE_NOISE_THRESH = 0.2  # everything under WHITE_NOISE_THRESH*avg_energy_per_freq is cut off
WINDOW_T_LEN = WINDOW_SIZE / SAMPLE_FREQ  # length of the window in seconds
SAMPLE_T_LENGTH = 1 / SAMPLE_FREQ  # length between two samples in seconds
DELTA_FREQ = SAMPLE_FREQ / WINDOW_SIZE  # frequency step width of the interpolated DFT
OCTAVE_BANDS = [50, 100, 200, 400, 800, 1600, 3200, 6400, 12800, 25600]  # octave bands for the frequency calculation
ALL_NOTES = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]  # there are 12 notes in an octave
