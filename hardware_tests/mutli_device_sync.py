import sys
sys.path.extend(["release_build/lib/", "debug_build/lib/", "build/lib/"])
import usrp_pybinding
from utils import RandomSignal, findFirstSampleInFrameOfSignal, dumpSamples

NO_TX_SAMPLES = 10e3
NO_RX_SAMPLES = 60e3

txSignal = RandomSignal()
txSignal.create(NO_TX_SAMPLES, 1)

rfConfig = usrp_pybinding.RfConfig()    
rfConfig.txGain = [50]
rfConfig.rxGain = [30]
rfConfig.txCarrierFrequency = [2e9]
rfConfig.rxCarrierFrequency = [2e9]
rfConfig.txAnalogFilterBw = 400e6
rfConfig.rxAnalogFilterBw = 400e6
rfConfig.txSamplingRate = 10e6
rfConfig.rxSamplingRate = 10e6

rxStreamingConfig = usrp_pybinding.RxStreamingConfig()
rxStreamingConfig.noSamples = NO_RX_SAMPLES
rxStreamingConfig.receiveTimeOffset = 2.0

txStreamingConfig = usrp_pybinding.TxStreamingConfig()
txStreamingConfig.samples = [txSignal.samples]
txStreamingConfig.sendTimeOffset = 2.0

ip = "localhost"
usrp = usrp_pybinding.createUsrp(ip)
usrp.setRfConfig(rfConfig)
usrp.setRxConfig(rxStreamingConfig)
_ = input("Press enter to synchronize devices and to continue")
usrp.setTimeToZeroNextPps()
samples = usrp.execute(0.0)
print(f"Tx signal starts at sample {findFirstSampleInFrameOfSignal(samples[0], txSignal.samples)} in the received frame.")
dumpSamples("rxSamples.csv", samples[0])
usrp.reset()