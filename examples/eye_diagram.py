"""Example shows how to use one USRP to draw an eye diagram of a
BPSK signal, using a sinc-filter as transmit filter.

Usage:
python eye_diagram.py --carrier-frequency 3.7e9 --usrp1-ip a.b.c.d --usrp2-ip <notused> --plot
"""

import matplotlib.pyplot as plt

import numpy as np

from usrp_client.system import System
from uhd_wrapper.utils.config import (
    RfConfig,
    TxStreamingConfig,
    RxStreamingConfig,
    MimoSignal,
)
from examples.helpers import readArgs


def createSystem(
        fc: float, txGain: float, rxGain: float, ipUsrp1: str) -> System:

    rfConfig = RfConfig()
    rfConfig.rxAnalogFilterBw = 400e6
    rfConfig.txAnalogFilterBw = 400e6
    rfConfig.rxSamplingRate = Fs
    rfConfig.txSamplingRate = Fs
    rfConfig.rxGain = rxGain
    rfConfig.txGain = txGain
    rfConfig.rxCarrierFrequency = fc
    rfConfig.txCarrierFrequency = fc
    rfConfig.noRxStreams = 1
    rfConfig.noTxStreams = 1

    # ceate system
    system = System()
    dev = system.newUsrp(ip=ipUsrp1, usrpName="usrp1")
    dev.configureRfConfig(rfConfig)
    return system


# How many signal samples are used for one bit
# (i.e. symbol in BPSK). signal bandwidth B = Fs/samplesPerBit
samplesPerBit = 20
numBits = 500       # how many bits to put into the signal
Fs = 122.88e6       # Sampling frequency to use
filterLen = 8       # length of sinc filter (double-sided) in number of symbols


def createTxSignal() -> np.ndarray:
    bits = 1 - 2 * (np.random.randn(numBits) > 0).astype(int)

    Ts = samplesPerBit / Fs
    t = np.arange(samplesPerBit * filterLen) / Fs

    args = (t-filterLen/2*Ts)/Ts
    g = np.sinc(args)

    ups = np.zeros(numBits * samplesPerBit)
    ups[samplesPerBit * np.arange(numBits)] = bits

    signal = np.convolve(g, ups)
    signal = signal / signal.max()

    if len(signal) % 2 == 1:
        signal = signal[:-1]
    return signal


def main() -> None:
    args = readArgs()

    system = createSystem(
        fc=args.carrier_frequency,
        txGain=30,
        rxGain=30,
        ipUsrp1=args.usrp1_ip,
    )

    for _ in range(3):
        txSignal = createTxSignal()
        system.configureTx(
            usrpName="usrp1",
            txStreamingConfig=TxStreamingConfig(samples=MimoSignal(signals=[txSignal]),
                                                sendTimeOffset=0.0))
        system.configureRx(
            usrpName="usrp1",
            rxStreamingConfig=RxStreamingConfig(
                noSamples=len(txSignal)+1000, receiveTimeOffset=0.0))

        system.execute()
        samples = system.collect()
        rxSignal = samples["usrp1"][0].signals[0]

        if args.plot:
            plt.subplot(221)
            plt.title("TX and RX signal, real part")
            plt.plot(txSignal.real, label="Tx signal")
            plt.plot(rxSignal.real, label="Rx signal")
            plt.grid(True)
            plt.legend()

            plt.subplot(223)
            fTx = np.linspace(-0.5, 0.5, len(txSignal))
            sTx = np.fft.fftshift(20*np.log10(abs(np.fft.fft(txSignal))))
            fRx = np.linspace(-0.5, 0.5, len(rxSignal))
            sRx = np.fft.fftshift(20*np.log10(abs(np.fft.fft(rxSignal))))
            plt.title("TX and RX spectrum")
            plt.plot(fTx, sTx, label="TX signal")
            plt.plot(fRx, sRx, label="RX signal")
            plt.grid(True)
            plt.axvline(1/(2*samplesPerBit), color='k', alpha=0.5, label='+- B/2')
            plt.axvline(-1/(2*samplesPerBit), color='k', alpha=0.5)
            plt.legend()

            plt.subplot(222)
            start = int(filterLen / 2 * samplesPerBit + 10 * samplesPerBit)
            end = start + (numBits-10) * samplesPerBit

            plt.plot(txSignal[start:end].reshape(-1, 2*samplesPerBit).T, 'b')
            plt.grid(True)
            plt.title("Eye Diagram TX signal")

            plt.subplot(224)
            plt.plot(rxSignal[start:end].reshape(-1, 2*samplesPerBit).T.real, 'b')
            plt.title("Eye Diagram Rx signal, not time-synchronized")
            plt.grid(True)

            plt.show()


if __name__ == "__main__":
    main()
