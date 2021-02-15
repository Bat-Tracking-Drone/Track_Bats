from rtlsdr import *

import sys
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import mlab
import time

sdr = RtlSdr()

sdr.sample_rate = 2.4e6
sdr.center_freq = 150.5e6
sdr.gain = 5

num_samples = 512*2048

samples = sdr.read_samples(num_samples)
Pxx, freqs = mlab.psd(samples, Fs=sdr.sample_rate)
freqs+=sdr.center_freq

amplitude_dB = 10 * np.log10(np.abs(Pxx))

original_stdout = sys.stdout 

with open('filename.txt', 'a') as f:
    sys.stdout = f
    res = "\n".join("{} {}".format(x, y) for x, y in zip(freqs, amplitude_dB))
    print(res)
    sys.stdout = original_stdout

