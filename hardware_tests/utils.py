import numpy as np
import csv

def createZadoffChuChirp(N: int) -> np.array:
    M = 1
    cF = N%2
    q = 0
    return np.array([np.exp(-1j*np.pi*M*k*(k+cF + q) / N) for k in range(N)])


def getFirstSampleOfSignal(frame: np.array, signal: np.array) -> int:
    correlation = np.abs(np.correlate(frame, signal))
    return np.argsort(correlation)[-1]

def dumpSamples(csvName: str, samples: np.array) -> None:
    with open(csvName, 'w') as f:
        csvWriter = csv.writer(f)
        for sample in samples.tolist():
            csvWriter.writerow([sample])