from typing import Tuple
import logging
import time

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


logging.basicConfig(level=logging.INFO)
c = RfConfig()
c.rxAnalogFilterBw = 400e6
c.txAnalogFilterBw = 400e6
c.rxSamplingRate = 245.76e6 / 2
c.txSamplingRate = 245.76e6 / 2
c.rxGain = [35]
c.txGain = [35]
c.rxCarrierFrequency = [2e9]
c.txCarrierFrequency = [2e9]

txSignal = createRandom(int(20e3), zeropad=2000)
txStreamingConfig1 = TxStreamingConfig(sendTimeOffset=0.0, samples=[txSignal])
rxStreamingConfig1 = RxStreamingConfig(receiveTimeOffset=0.1, noSamples=int(60e3))

txStreamingConfig2 = TxStreamingConfig(sendTimeOffset=0.1, samples=[txSignal])
rxStreamingConfig2 = RxStreamingConfig(receiveTimeOffset=0.0, noSamples=int(60e3))

system = System()
system.addUsrp(rfConfig=c, ip="192.168.189.133", usrpName="usrp1")
system.addUsrp(rfConfig=c, ip="192.168.189.131", usrpName="usrp2")

for iteration in range(3):
    start = time.time()
    system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig1)
    print(f"Config 1 Took {time.time() - start} seconds")
    system.configureRx(usrpName="usrp1", rxStreamingConfig=rxStreamingConfig1)
    print(f"Config 1RX Took {time.time() - start} seconds")

    system.configureTx(usrpName="usrp2", txStreamingConfig=txStreamingConfig2)
    system.configureRx(usrpName="usrp2", rxStreamingConfig=rxStreamingConfig2)
    print(f"Config 2 Took {time.time() - start} seconds")

    system.execute()
    print(f"EXecute Took {time.time() - start} seconds")

    samples = system.collect()
    print(f"Took {time.time() - start} seconds")

    txSignalStartUsrp2, correlationUsrp2 = findFirstSampleInFrameOfSignal(
        samples["usrp2"][0], txSignal
    )

    txSignalStartUsrp1, correlationUsrp1 = findFirstSampleInFrameOfSignal(
        samples["usrp1"][0], txSignal
    )

    print(f"Sent signal from usrp2 starts at sample {txSignalStartUsrp1} in usrp1")
    print(f"Sent signal from usrp1 starts at sample {txSignalStartUsrp2} in usrp2")

    plt.subplot(221)
    plt.plot(np.arange(60e3), np.abs(samples["usrp1"][0]))
    plt.title("Received samples usrp1")
    plt.subplot(222)
    plt.plot(np.arange(60e3), np.abs(samples["usrp2"][0]))
    plt.title("Received samples usrp2")
    plt.subplot(223)
    plt.plot(np.arange(correlationUsrp1.size), np.abs(correlationUsrp1))
    plt.subplot(224)
    plt.plot(np.arange(correlationUsrp2.size), np.abs(correlationUsrp2))
    plt.show()
