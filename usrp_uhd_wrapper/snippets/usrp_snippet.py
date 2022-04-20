import sys
sys.path.extend(["release_build/lib/", "debug_build/lib/", "build/lib/"])
import usrp_pybinding
import numpy as np

rfConfig = usrp_pybinding.RfConfig()    
rfConfig.txGain = [50];
rfConfig.rxGain = [30];
rfConfig.txCarrierFrequency = [2e9];
rfConfig.rxCarrierFrequency = [2e9];
rfConfig.txAnalogFilterBw = 400e6;
rfConfig.rxAnalogFilterBw = 400e6;
rfConfig.txSamplingRate = 10e6;
rfConfig.rxSamplingRate = 10e6;

rxStreamingConfig = usrp_pybinding.RxStreamingConfig()
rxStreamingConfig.noSamples = int(60e3)
rxStreamingConfig.receiveTimeOffset = 2.0

txStreamingConfig = usrp_pybinding.TxStreamingConfig()
txStreamingConfig.samples = [3*np.ones(int(60e3), dtype=complex)]
txStreamingConfig.sendTimeOffset = 2.0

ip = "localhost"
usrp = usrp_pybinding.createUsrp(ip)
usrp.setRfConfig(rfConfig)
usrp.setRxConfig(rxStreamingConfig)
usrp.setTimeToZeroNextPps()
usrp.execute(0.0)
samples = usrp.collect()
usrp.reset()
