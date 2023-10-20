# This example runs a single OFDM frame without CP and wtih no channel
# estimation/equalization. It shows the unequalized constellation at the RX
# side, along with the channel phase and amplitude. Parameters to adjust: Fs,
# Fc, delay, N, Non, ip

import numpy as np
import matplotlib.pyplot as plt

from usrp_client.system import System
from uhd_wrapper.utils.config import (
    RfConfig,
    TxStreamingConfig,
    RxStreamingConfig,
    MimoSignal,
)


def createSystem(
        fc: float, fs: float, txGain: float, rxGain: float, ipUsrp1: str) -> System:

    rfConfig = RfConfig()
    rfConfig.rxAnalogFilterBw = 400e6
    rfConfig.txAnalogFilterBw = 400e6
    rfConfig.rxSamplingRate = fs
    rfConfig.txSamplingRate = fs
    rfConfig.rxGain = rxGain
    rfConfig.txGain = txGain
    rfConfig.rxCarrierFrequency = fc
    rfConfig.txCarrierFrequency = fc
    rfConfig.noRxAntennas = 1
    rfConfig.noTxAntennas = 1

    # ceate system
    system = System()
    dev = system.newUsrp(ip=ipUsrp1, usrpName="usrp1")
    dev.configureRfConfig(rfConfig)
    return system


ip = "192.168.199.134"  # IP of the USRP to attach to
Fc = 3.7e9   # Carrier frequenc
Fs = 2*245.76e6   # Sampling rate

delay = 363        # Delay of RX towards TX in samples. Get e.g. by running
# python -m usrp_client.sanity --ips 192.168.199.134  --single  --sync --fs 491.52e6 --fc 3.7e9

padding = 1000  # How many zeros to append to the beginning of the frame to let RF ramp up

N = 2048  # Number of subcarriers
Non = 1200   # Number of switched-on subcarriers
Noff = N - Non

II = 1 - 2 * (np.random.randn(N) > 0)
QQ = 1 - 2 * (np.random.randn(N) > 0)

IQ = II + 1j*QQ
IQ[:Noff//2] = 0
IQ[-Noff//2:] = 0

txSym = np.fft.ifft(np.fft.fftshift(IQ))

txSig = np.zeros(40000, dtype=complex)
txSig[padding:padding+N] = txSym
txSig = txSig / max(abs(txSig))


system = createSystem(fc=Fc, fs=Fs, txGain=30, rxGain=30, ipUsrp1=ip)
system.configureTx(usrpName="usrp1",
                   txStreamingConfig=TxStreamingConfig(samples=MimoSignal(signals=[txSig]),
                                                       sendTimeOffset=0.0))
system.configureRx(usrpName="usrp1", rxStreamingConfig=RxStreamingConfig(
    noSamples=len(txSig), receiveTimeOffset=0.0))

system.execute()
samples = system.collect()


rxSig = samples["usrp1"][0].signals[0]

rxSym = rxSig[padding+delay:padding+delay+N]
demod = np.fft.fftshift(np.fft.fft(rxSym))


f = np.arange(-N//2, N//2)

plt.figure()
plt.plot(demod.real, demod.imag, 'x')

plt.figure()
plt.subplot(211)
H = demod / (IQ+0.01)
plt.title("Channel phase")
plt.plot(f, np.angle(H))
plt.axvline(-Non//2, color='k')
plt.axvline(Non//2, color='k')

plt.subplot(212)
plt.title("Channel Amplitude")
plt.plot(f, abs(H))
plt.axvline(-Non//2, color='k')
plt.axvline(Non//2, color='k')
plt.show()
