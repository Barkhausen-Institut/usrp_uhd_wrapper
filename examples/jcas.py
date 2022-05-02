from typing import Tuple
import argparse

import numpy as np
import matplotlib.pyplot as plt

from usrp_client.system import System
from uhd_wrapper.utils.config import RfConfig, TxStreamingConfig, RxStreamingConfig


def createChirp(
    fStart: float,
    fStop: float,
    fSampling: float,
    noSamples: int,
    amplitude: float = 1.0,
) -> np.ndarray:
    t = np.arange(noSamples) / fSampling
    f = np.linspace(fStart, fStop, noSamples)
    return amplitude * np.exp(1j * 2 * np.pi * f * t)


def findFirstSampleInFrameOfSignal(
    frame: np.ndarray, txSignal: np.ndarray
) -> Tuple[int, np.ndarray]:
    correlation = np.abs(np.correlate(frame, txSignal))
    return np.argsort(correlation)[-1], correlation


parser = argparse.ArgumentParser()
parser.add_argument(
    "--plot",
    type=bool,
    default=False,
    help="Plot received singals in time and frequency",
)
args = parser.parse_args()
NO_RX_SAMPLES = 60e3
NO_TX_SAMPLES = int(20e3)

# create signal to be se nt
txSignal = createChirp(
    fStart=-25e6, fStop=25e6, fSampling=50e6, noSamples=NO_TX_SAMPLES
)

# create configurations
rfConfig = RfConfig()
rfConfig.rxAnalogFilterBw = 400e6
rfConfig.txAnalogFilterBw = 400e6
rfConfig.rxSamplingRate = 245.76e6 / 2
rfConfig.txSamplingRate = 245.76e6 / 2
rfConfig.rxGain = [35]
rfConfig.txGain = [35]
rfConfig.rxCarrierFrequency = [2e9]
rfConfig.txCarrierFrequency = [2e9]

txStreamingConfig1 = TxStreamingConfig(sendTimeOffset=1.0, samples=[txSignal])
rxStreamingConfig1 = RxStreamingConfig(
    receiveTimeOffset=1.0, noSamples=int(NO_RX_SAMPLES)
)

rxStreamingConfig2 = RxStreamingConfig(
    receiveTimeOffset=1.0, noSamples=int(NO_RX_SAMPLES)
)


# ceate system
system = System()
system.addUsrp(rfConfig=rfConfig, ip="192.168.189.131", usrpName="usrp1")
system.addUsrp(rfConfig=rfConfig, ip="192.168.189.133", usrpName="usrp2")

system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig1)
system.configureRx(usrpName="usrp1", rxStreamingConfig=rxStreamingConfig1)

system.configureRx(usrpName="usrp2", rxStreamingConfig=rxStreamingConfig2)

system.execute()
samples = system.collect()
txSignalStartUsrp2, correlationUsrp2 = findFirstSampleInFrameOfSignal(
    samples["usrp2"][0], txSignal
)

txSignalStartUsrp1, correlationUsrp1 = findFirstSampleInFrameOfSignal(
    samples["usrp1"][0], txSignal
)

print(f"Sent chirp from usrp2 starts at sample {txSignalStartUsrp1} in usrp1")
print(f"Sent chirp from usrp1 starts at sample {txSignalStartUsrp2} in usrp2")

if args.plot:
    rxSpectrumUsrp1 = np.fft.fftshift(np.fft.fft(samples["usrp1"][0]))
    rxFreqSpectrumUsrp1 = np.fft.fftshift(np.fft.fftfreq(samples["usrp1"][0].size))

    rxSpectrumUsrp2 = np.fft.fftshift(np.fft.fft(samples["usrp2"][0]))
    rxFreqSpectrumUsrp2 = np.fft.fftshift(np.fft.fftfreq(samples["usrp2"][0].size))
    plt.subplot(221)
    plt.plot(np.arange(NO_RX_SAMPLES), samples["usrp1"][0])
    plt.xlabel("Samples [#]")
    plt.ylabel("Value")
    plt.title("Usrp1, received samples, time")

    plt.subplot(222)
    plt.plot(np.arange(NO_RX_SAMPLES), samples["usrp2"][0])
    plt.xlabel("Samples [#]")
    plt.ylabel("Value")
    plt.title("Usrp2, received samples, time")

    plt.subplot(223)
    plt.semilogy(rxFreqSpectrumUsrp1 / 1e6, np.abs(rxSpectrumUsrp1))
    plt.xlabel("Frequency [Mhz]")
    plt.ylabel("Power [log]")
    plt.title("Spectrum USRP1")

    plt.subplot(224)
    plt.semilogy(rxFreqSpectrumUsrp2 / 1e6, np.abs(rxSpectrumUsrp2))
    plt.xlabel("Frequency [Mhz]")
    plt.ylabel("Power [log]")
    plt.title("Spectrum USRP2")
    plt.show()
