import unittest
from unittest.mock import patch, Mock

from uhd_wrapper.rpc_server.reconfigurable_usrp import MimoReconfiguringUsrp
from uhd_wrapper.usrp_pybinding import RfConfig
from uhd_wrapper.utils.config import fillDummyRfConfig


class TestMimoReconfigUsrp(unittest.TestCase):
    def setUp(self) -> None:
        self.usrpIp = "localhost"
        usrpFactoryPatcher = patch(
            "uhd_wrapper.usrp_pybinding.createUsrp", return_value=Mock()
        )
        self.mockedUsrpFactoryFunction = usrpFactoryPatcher.start()
        self.M = MimoReconfiguringUsrp(self.usrpIp)
        self.mockedUsrpFactoryFunction.reset_mock()

    def test_mimoConfigChanges_usrpRestarted(self) -> None:
        sisoRfConfig = fillDummyRfConfig(RfConfig())
        mimoRfConfig = fillDummyRfConfig(RfConfig())
        mimoRfConfig.noRxAntennas = 2
        mimoRfConfig.noTxAntennas = 4

        self.M.setRfConfig(sisoRfConfig)
        self.M.setRfConfig(mimoRfConfig)
        self.mockedUsrpFactoryFunction.assert_called_once_with(self.usrpIp)

    def test_mimoConfigNotChanged_usrpNotRestarted(self) -> None:
        sisoRfConfig = fillDummyRfConfig(RfConfig())
        self.M.setRfConfig(sisoRfConfig)
        self.M.setRfConfig(sisoRfConfig)
        self.mockedUsrpFactoryFunction.assert_not_called()
