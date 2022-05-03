from typing import Tuple, Dict, List

import numpy as np
import matplotlib.pyplot as plt


def createRandom(noSamples: int, zeropad: int = 0) -> np.ndarray:
    return np.hstack(
        [
            np.zeros(zeropad, dtype=complex),
            np.random.rand(noSamples) + 1j * np.random.rand(noSamples),
        ]
    )


def findFirstSampleInFrameOfSignal(
    frame: np.ndarray, txSignal: np.ndarray
) -> Tuple[int, np.ndarray]:
    correlation = np.abs(np.correlate(frame, txSignal))
    return np.argsort(correlation)[-1], correlation


def printDelays(samples: Dict[str, List[np.ndarray]], txSignal: np.ndarray) -> None:
    txSignalStartUsrp2, _ = findFirstSampleInFrameOfSignal(
        samples["usrp2"][0], txSignal
    )
    txSignalStartUsrp1, _ = findFirstSampleInFrameOfSignal(
        samples["usrp1"][0], txSignal
    )

    print(f"Sent chirp from usrp2 starts at sample {txSignalStartUsrp1} in usrp1")
    print(f"Sent chirp from usrp1 starts at sample {txSignalStartUsrp2} in usrp2")


def db(data: np.ndarray) -> np.ndarray:
    return 20 * np.log10(np.abs(data))


def plot(samples: Dict[str, List[np.ndarray]]) -> None:
    noRxSamples = samples["usrp1"][0].size
    rxSpectrumUsrp1 = np.fft.fftshift(np.fft.fft(samples["usrp1"][0]))
    rxFreqSpectrumUsrp1 = np.fft.fftshift(np.fft.fftfreq(noRxSamples))

    rxSpectrumUsrp2 = np.fft.fftshift(np.fft.fft(samples["usrp2"][0]))
    rxFreqSpectrumUsrp2 = np.fft.fftshift(np.fft.fftfreq(noRxSamples))
    plt.subplot(221)
    plt.plot(np.arange(noRxSamples), samples["usrp1"][0])
    plt.xlabel("Samples [#]")
    plt.ylabel("Value")
    plt.title("Usrp1, received samples, time")

    plt.subplot(222)
    plt.plot(np.arange(noRxSamples), samples["usrp2"][0])
    plt.xlabel("Samples [#]")
    plt.ylabel("Value")
    plt.title("Usrp2, received samples, time")

    plt.subplot(223)
    plt.plot(rxFreqSpectrumUsrp1 / 1e6, db(rxSpectrumUsrp1))
    plt.xlabel("Frequency [Mhz]")
    plt.ylabel("Power [dB]")
    plt.title("Spectrum USRP1")

    plt.subplot(224)
    plt.plot(rxFreqSpectrumUsrp2 / 1e6, db(rxSpectrumUsrp2))
    plt.xlabel("Frequency [Mhz]")
    plt.ylabel("Power [dB]")
    plt.title("Spectrum USRP2")
    plt.show()
