from curses.ascii import FS
import numpy as np
import csv
from abc import ABC, abstractmethod

class Signal(ABC):
    @abstractmethod
    def create(self, noSamples: int, amplitude: float) -> None:
        pass

class ZadoffChuChirp(Signal):
    def create(self, noSamples: int, amplitude: float) -> None:
        N = noSamples
        M = 1
        cF = N%2
        q = 0
        self.samples = np.array([amplitude*np.exp(-1j*np.pi*M*k*(k+cF + q) / N) for k in range(N)]) 

class RectSignal(Signal):
    def create(self, noSamples: int, amplitude: float) -> None:
        self.samples = amplitude * np.ones(noSamples, dtype=np.complex64)

class RandomSignal(Signal):
    def create(self, noSamples: int, ampltitude: float) -> None:
        self.samples = ampltitude*(2 * (np.random.sample((noSamples,)) + 1j * np.random.sample((noSamples,))) - (
            1 + 1j
        ))

class FrequencyZOH(Signal):
    def __init__(self, noSignals: float, fStart: float, fStop: float, fSampling: float):
        self.__noSignals= noSignals
        self.__fStart = fStart
        self.__fStop = fStop
        self.__fSampling = fSampling

    def create(self, noSamples: int, amplitude: float) -> None:
        zohLength = noSamples // self.__noSignals
        frequencies = np.linspace(self.__fStart, self.__fStop, self.__noSignals)
        frame = np.arange(noSamples, dtype=np.complex64) / self.__fSampling
        frame[zohLength * self.__noSignals:] = 0
        for fIdx in range(self.__noSignals):
            timeStamps = frame[fIdx * zohLength : (fIdx + 1) * zohLength]
            frame[fIdx * zohLength : (fIdx + 1) * zohLength] = amplitude*np.exp(1j * 2 * np.pi * frequencies[fIdx] * timeStamps)
        self.samples = frame

def findFirstSampleInFrameOfSignal(frame: np.array, txSignal: np.array) -> int:
    correlation = np.abs(np.correlate(frame, txSignal))
    return np.argsort(correlation)[-1]

def dumpSamples(csvName: str, samples: np.array) -> None:
    with open(csvName, 'w') as f:
        csvWriter = csv.writer(f)
        for sample in samples.tolist():
            csvWriter.writerow([sample])