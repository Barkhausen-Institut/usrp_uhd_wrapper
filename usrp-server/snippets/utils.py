import csv

import numpy as np


def findFirstSampleInFrameOfSignal(frame: np.array, txSignal: np.array) -> int:
    correlation = np.abs(np.correlate(frame, txSignal))
    return np.argsort(correlation)[-1]

def dumpSamples(csvName: str, samples: np.array) -> None:
    with open(csvName, 'w') as f:
        csvWriter = csv.writer(f)
        for sample in samples.tolist():
            csvWriter.writerow([sample])