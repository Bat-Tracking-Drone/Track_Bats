from rtlsdr import *
from pylab import *
import time

sdr = RtlSdr()

# configure device
sdr.sample_rate = 2.048e6  # Hz
sdr.center_freq = 250e6     # Hz
sdr.gain = 4

for i in range(1000):
	samples = sdr.read_samples(512)
	print(10*log10(var(samples)))
	time.sleep(0.5)
