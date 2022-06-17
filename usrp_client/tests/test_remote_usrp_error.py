import unittest

from usrp_client.remote_usrp_error import RemoteUsrpError


class TestRemoteUsrpError(unittest.TestCase):
    def test_standardExceptionContainsEmptyUsrpField(self) -> None:
        error = RemoteUsrpError("foo")
        self.assertEqual(error.usrpName, "")

    def test_msgCreatedWithUsrpName(self) -> None:
        usrpName = "usrp1"
        error = RemoteUsrpError("foo", usrpName)
        self.assertIn(usrpName, str(error))
