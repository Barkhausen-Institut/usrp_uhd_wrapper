from typing import Tuple
import argparse

import numpy as np
import matplotlib.pyplot as plt

from usrp_client.system import System
from uhd_wrapper.utils.config import RfConfig, TxStreamingConfig, RxStreamingConfig
from examples.utils import createRandom, findFirstSampleInFrameOfSignal


parser = argparse.ArgumentParser()
parser.add_argument("--usrp1-ip", type=str, help="IP of first USRP")
parser.add_argument("--usrp2-ip", type=str, help="IP of second USRP")
parser.add_argument(
    "--carrier-frequency", type=float, help="Carrier frequency of sent signal"
)
parser.add_argument(
    "--plot",
    type=bool,
    default=False,
    help="Plot received singals in time and frequency",
)
args = parser.parse_args()

# create signal to be se nt
txSignal = createRandom(int(20e3), zeropad=2000)

# create configurations
NO_RX_SAMPLES = 60e3
rfConfig = RfConfig()
rfConfig.rxAnalogFilterBw = 400e6
rfConfig.txAnalogFilterBw = 400e6
rfConfig.rxSamplingRate = 245.76e6 / 2
rfConfig.txSamplingRate = 245.76e6 / 2
rfConfig.rxGain = [35]
rfConfig.txGain = [35]
rfConfig.rxCarrierFrequency = [args.carrier_frequency]
rfConfig.txCarrierFrequency = [args.carrier_frequency]

txStreamingConfig1 = TxStreamingConfig(sendTimeOffset=0.0, samples=[txSignal])
rxStreamingConfig1 = RxStreamingConfig(
    receiveTimeOffset=0.1, noSamples=int(NO_RX_SAMPLES)
)

txStreamingConfig2 = TxStreamingConfig(sendTimeOffset=0.1, samples=[txSignal])
rxStreamingConfig2 = RxStreamingConfig(
    receiveTimeOffset=0.0, noSamples=int(NO_RX_SAMPLES)
)

# ceate system
system = System()
system.addUsrp(rfConfig=rfConfig, ip=args.usrp1_ip, usrpName="usrp1")
system.addUsrp(rfConfig=rfConfig, ip=args.usrp2_ip, usrpName="usrp2")

system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig1)
system.configureRx(usrpName="usrp1", rxStreamingConfig=rxStreamingConfig1)

system.configureTx(usrpName="usrp2", txStreamingConfig=txStreamingConfig2)
system.configureRx(usrpName="usrp2", rxStreamingConfig=rxStreamingConfig2)

system.execute()
samples = system.collect()
txSignalStartUsrp2, correlationUsrp2 = findFirstSampleInFrameOfSignal(
    samples["usrp2"][0], txSignal
)

txSignalStartUsrp1, correlationUsrp1 = findFirstSampleInFrameOfSignal(
    samples["usrp1"][0], txSignal
)

print(f"Sent random signal from usrp2 starts at sample {txSignalStartUsrp1} in usrp1")
print(f"Sent random signal from usrp1 starts at sample {txSignalStartUsrp2} in usrp2")

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
