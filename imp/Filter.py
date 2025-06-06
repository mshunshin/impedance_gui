import numpy as np
from scipy.signal import butter, lfilter, freqz
import matplotlib.pyplot as plt

class Filter:
    def butter_lowpass_filter(data, cutoff, fs, order):
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype='lowpass', analog=False)
        y = lfilter(b, a, data)
        return y
        self.ButterLP=y


    def butter_highpass_filter(data,cutoff,fs,order):
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype='highpass', analog=False)
        y = lfilter(b, a, data)
        return y


    def butter_bandpass_filter(data,cutoff,fs,order):
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype='bandpass', analog=False)
        y = lfilter(b, a, data)
        return y