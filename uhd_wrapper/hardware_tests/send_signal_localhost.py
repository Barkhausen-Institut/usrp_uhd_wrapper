import sys
sys.path.extend(["release_build/lib/", "debug_build/lib/", "build/lib/"])
import usrp_pybinding
from copy import deepcopy
from .utils import (RandomSignal, findFirstSampleInFrameOfSignal, dumpSamples)


NO_TX_SAMPLES = int(10e3)
NO_RX_SAMPLES = int(60e3)
ip = "localhost"
usrp = usrp_pybinding.createUsrp(ip)
fSampling = usrp.getMasterClockRate() / 4

txSignal = RandomSignal()
txSignal.create(NO_TX_SAMPLES, 1)
rfConfig = usrp_pybinding.RfConfig()
rfConfig.txGain = [35]
rfConfig.rxGain = [35]
rfConfig.txCarrierFrequency = [2e9]
rfConfig.rxCarrierFrequency = [2e9]
rfConfig.txAnalogFilterBw = 400e6
rfConfig.rxAnalogFilterBw = 400e6
rfConfig.txSamplingRate = fSampling
rfConfig.rxSamplingRate = fSampling

rxStreamingConfig = usrp_pybinding.RxStreamingConfig()
rxStreamingConfig.noSamples = NO_RX_SAMPLES
rxStreamingConfig.receiveTimeOffset = 2.0

txStreamingConfig = usrp_pybinding.TxStreamingConfig()
txStreamingConfig.samples = [deepcopy(txSignal.samples)]
txStreamingConfig.sendTimeOffset = 2.0

usrp.setRfConfig(rfConfig)
usrp.setRxConfig(rxStreamingConfig)
usrp.setTxConfig(txStreamingConfig)
usrp.setTimeToZeroNextPps()
usrp.execute(0.0)
samples = usrp.collect()
usrp.reset()

# post-process
signalStartSample = findFirstSampleInFrameOfSignal(samples[0], txSignal.samples)
print(f"The siganl starts at sample {signalStartSample}")
dumpSamples("rxSamples.csv", samples[0])
dumpSamples("txSamples.csv", txSignal.samples)
