import sys
sys.path.extend(["release_build/lib/", "debug_build/lib/", "build/lib/"])
import usrp_pybinding
import numpy as np

def createZadoffChuChirp(N: int) -> np.array:
    M = N+1
    if (N % 2 == 0):
        x = np.array([np.exp(1j*np.pi*M*k**2/N) for k in range(N)])
    else:
        x = np.array([np.exp(1j*np.pi*M*k*(k+1)/N) for k in range(N)])
    return x

def getSignalLength(correlation: np.array) -> int:
    ind1 = abs(np.argsort(correlation)[-1])
    ind2 = abs(np.argsort(correlation)[-2])
    
    signalEnd = ind1 if ind1 > ind2 else ind1
    signalStart = ind1 if ind1 < ind2 else ind2
    return signalEnd - signalStart

NO_TX_SAMPLES = int(2e3)
NO_RX_SAMPLES = int(60e3)
txSignal = createZadoffChuChirp(NO_TX_SAMPLES)

rfConfig = usrp_pybinding.RfConfig()
rfConfig.txGain = [50];
rfConfig.rxGain = [30];
rfConfig.txCarrierFrequency = [2e9];
rfConfig.rxCarrierFrequency = [2e9];
rfConfig.txAnalogFilterBw = 400e6;
rfConfig.rxAnalogFilterBw = 400e6;
rfConfig.txSamplingRate = 50e6;
rfConfig.rxSamplingRate = 50e6;

rxStreamingConfig = usrp_pybinding.RxStreamingConfig()
rxStreamingConfig.noSamples = NO_RX_SAMPLES
rxStreamingConfig.receiveTimeOffset = 2.0

txStreamingConfig = usrp_pybinding.TxStreamingConfig()
txStreamingConfig.samples = [txSignal]
txStreamingConfig.sendTimeOffset = 2.0

ip = "localhost"
usrp = usrp_pybinding.createUsrp(ip)
usrp.setRfConfig(rfConfig)
usrp.setRxConfig(rxStreamingConfig)
usrp.setTxConfig(txStreamingConfig)
usrp.setTimeToZeroNextPps()
samples = usrp.execute(0.0)
usrp.reset()

# post-process
xcorr = np.abs(np.correlate(samples[0], txSignal))
signalStartSample = getSignalLength(xcorr)
print(f"The siganl starts at sample {signalStartSample}")
breakpoint()