import numpy as np
import matplotlib.pyplot as plt

from usrp_client.system import System
from uhd_wrapper.utils.config import RfConfig, TxStreamingConfig, RxStreamingConfig

c = RfConfig()
c.rxAnalogFilterBw = 400e6
c.txAnalogFilterBw = 400e6
c.rxSamplingRate = 250e6 / 4
c.txSamplingRate = 250e6 / 4
c.rxGain = [50]
c.txGain = [40]
c.rxCarrierFrequency = [2e9]
c.txCarrierFrequency = [2e9]

txStreamingConfig1 = TxStreamingConfig(sendTimeOffset=2.0, samples=[np.ones(int(10e3))])
rxStreamingConfig1 = RxStreamingConfig(receiveTimeOffset=2.1, noSamples=int(60e3))
txStreamingConfig2 = TxStreamingConfig(sendTimeOffset=2.1, samples=[np.ones(int(10e3))])
rxStreamingConfig2 = RxStreamingConfig(receiveTimeOffset=2.0, noSamples=int(60e3))
system = System()
system.addUsrp(rfConfig=c, ip="192.168.189.133", name="usrp1")
system.addUsrp(rfConfig=c, ip="192.168.189.131", name="usrp2")

system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig1)
system.configureRx(usrpName="usrp1", rxStreamingConfig=rxStreamingConfig1)

system.configureTx(usrpName="usrp2", txStreamingConfig=txStreamingConfig2)
system.configureRx(usrpName="usrp2", rxStreamingConfig=rxStreamingConfig2)
system.execute()
samples = system.collect()


plt.subplot(121)
plt.plot(np.arange(60e3), np.abs(samples[0][0]))
plt.subplot(122)
plt.plot(np.arange(60e3), np.abs(samples[1][0]))
plt.show()
