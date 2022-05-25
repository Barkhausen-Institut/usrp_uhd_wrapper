from typing import Tuple, Dict, List, Any
import argparse

import numpy as np
import matplotlib.pyplot as plt

from uhd_wrapper.utils.config import MimoSignal


def readArgs() -> Any:
    parser = argparse.ArgumentParser()
    parser.add_argument("--usrp1-ip", type=str, help="IP of first USRP", required=True)
    parser.add_argument("--usrp2-ip", type=str, help="IP of second USRP", required=True)
    parser.add_argument(
        "--carrier-frequency",
        type=float,
        help="Carrier frequency of sent signal",
        required=True,
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Plot received singals in time and frequency",
    )
    args = parser.parse_args()
    return args


def createRandom(noSamples: int, zeropad: int = 0) -> np.ndarray:
    return np.hstack(
        [
            np.zeros(zeropad, dtype=complex),
            2 * (np.random.sample((noSamples,)) + 1j * np.random.sample((noSamples,)))
            - (1 + 1j),
        ]
    )


def findFirstSampleInFrameOfSignal(
    frame: np.ndarray, txSignal: np.ndarray
) -> Tuple[int, np.ndarray]:
    correlation = np.abs(np.correlate(frame, txSignal))
    return np.argsort(correlation)[-1], correlation


def printDelays(samples: Dict[str, List[MimoSignal]], txSignal: np.ndarray) -> None:
    txSignalStartUsrp2, _ = findFirstSampleInFrameOfSignal(
        samples["usrp2"][0].signals[0], txSignal
    )
    txSignalStartUsrp1, _ = findFirstSampleInFrameOfSignal(
        samples["usrp1"][0].signals[0], txSignal
    )

    print(f"Sent chirp from usrp2 starts at sample {txSignalStartUsrp1} in usrp1")
    print(f"Sent chirp from usrp1 starts at sample {txSignalStartUsrp2} in usrp2")


def db(data: np.ndarray) -> np.ndarray:
    return 20 * np.log10(np.abs(data))


def plot(samples: Dict[str, List[MimoSignal]]) -> None:
    samplesUsrp1 = samples["usrp1"][0].signals[0]
    samplesUsrp2 = samples["usrp2"][0].signals[0]
    rxSpectrumUsrp1 = np.fft.fftshift(np.fft.fft(samplesUsrp1))

    rxSpectrumUsrp2 = np.fft.fftshift(np.fft.fft(samplesUsrp2))
    freq = np.linspace(-0.5, 0.5, samplesUsrp1.size, endpoint=False)
    plt.subplot(221)
    plt.plot(np.arange(samplesUsrp1.size), samplesUsrp1)
    plt.xlabel("Samples [#]")
    plt.ylabel("Value")
    plt.title("Usrp1, received samples, time")

    plt.subplot(222)
    plt.plot(np.arange(samplesUsrp1.size), samplesUsrp2)
    plt.xlabel("Samples [#]")
    plt.ylabel("Value")
    plt.title("Usrp2, received samples, time")

    plt.subplot(223)
    plt.plot(freq, db(rxSpectrumUsrp1))
    plt.xlabel("Frequency / fs")
    plt.ylabel("Power [dB]")
    plt.title("Spectrum USRP1")

    plt.subplot(224)
    plt.plot(freq, db(rxSpectrumUsrp2))
    plt.xlabel("Frequency / fs")
    plt.ylabel("Power [dB]")
    plt.title("Spectrum USRP2")
    plt.show()
