import numpy as np
import matplotlib.pyplot as plt

def createZadoffChuChirp(N: int) -> np.array:
    M = 1
    cF = N%2
    q = 0
    return np.array([np.exp(-1j*np.pi*M*k*(k+cF + q) / N) for k in range(N)])


def getFirstSampleOfSignal(frame: np.array, signal: np.array) -> int:
    correlation = np.abs(np.correlate(frame, signal))
    return np.argsort(correlation)[-1]


if __name__ == "__main__":
    NO_SAMPLES_FRAME = int(2e3)
    FIRST_SAMPLE_CHIRP = 62
    LENGTH_CHIRP = NO_SAMPLES_FRAME - FIRST_SAMPLE_CHIRP
    chirp = createZadoffChuChirp(LENGTH_CHIRP)
    frame = np.zeros(NO_SAMPLES_FRAME, dtype=np.complex64)
    frame[FIRST_SAMPLE_CHIRP:] = chirp

    print(getFirstSampleOfSignal(frame, chirp))
    plt.figure()
    plt.plot(np.arange(NO_SAMPLES_FRAME), np.real(frame))
    plt.plot(np.arange(NO_SAMPLES_FRAME), np.imag(frame))
    plt.show()