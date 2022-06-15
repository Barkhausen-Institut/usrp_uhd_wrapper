import unittest

from zerorpc.exceptions import RemoteError

from uhd_wrapper.utils.remote_usrp_error import RemoteUsrpError


def raiseRemoteError(msg: str) -> None:
    raise RemoteError(msg)


def handleRemoteError(msg: str, usrpName: str = "") -> None:
    try:
        raiseRemoteError(msg)
    except Exception as e:
        if usrpName == "":
            raise RemoteUsrpError(e.msg)
        else:
            raise RemoteUsrpError(e.msg, usrpName)


class TestRemoteUsrpError(unittest.TestCase):
    def test_standardExceptionContainsEmptyUsrpField(self) -> None:
        try:
            handleRemoteError("foo")
        except RemoteUsrpError as e:
            self.assertEqual(e.usrpName, "")

    def test_msgCreatedWithUsrpExceptionMsg(self) -> None:
        DUMMY_MSG = "foo"
        USRP_NAME = "usrp1"
        try:
            handleRemoteError(DUMMY_MSG, USRP_NAME)
        except RemoteUsrpError as e:
            self.assertIn(USRP_NAME, str(e))

    def test_msgContainsMsgOfReraisedException(self) -> None:
        DUMMY_MSG = "foo"
        try:
            handleRemoteError(DUMMY_MSG, "usrp1")
        except RemoteUsrpError as e:
            self.assertIn(DUMMY_MSG, str(e))
