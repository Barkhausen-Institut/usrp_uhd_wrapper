from typing import Tuple
import logging
import time
import argparse

import numpy as np
import matplotlib.pyplot as plt

from usrp_client.system import System
from uhd_wrapper.utils.config import RfConfig, TxStreamingConfig, RxStreamingConfig


def createRandom(noSamples: int, zeropad: int = 0) -> np.ndarray:
    return np.hstack(
        [
            np.zeros(zeropad, dtype=complex),
            np.random.rand(noSamples) + 1j * np.random.rand(noSamples),
        ]
    )


def createRamp(noSamples: int, zeropad: int = 0) -> np.ndarray:
    return np.hstack(
        [np.zeros(zeropad, dtype=complex), np.linspace(0, 1, noSamples, endpoint=False)]
    )


def createZadoffChu(noSamples: int) -> np.ndarray:
    N = noSamples
    cF = noSamples % 2
    q = 0
    k = np.arange(N)
    return np.exp(-1j * np.pi * (k * (k + cF + q)) / N)


def findFirstSampleInFrameOfSignal(
    frame: np.ndarray, txSignal: np.ndarray
) -> Tuple[int, np.ndarray]:
    correlation = np.abs(np.correlate(frame, txSignal))
    return np.argsort(correlation)[-1], correlation


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
rxStreamingConfig1 = RxStreamingConfig(receiveTimeOffset=0.1, noSamples=int(60e3))

txStreamingConfig2 = TxStreamingConfig(sendTimeOffset=0.1, samples=[txSignal])
rxStreamingConfig2 = RxStreamingConfig(receiveTimeOffset=0.0, noSamples=int(60e3))

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

print(f"Sent signal from usrp2 starts at sample {txSignalStartUsrp1} in usrp1")
print(f"Sent signal from usrp1 starts at sample {txSignalStartUsrp2} in usrp2")
