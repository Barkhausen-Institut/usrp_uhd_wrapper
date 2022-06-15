import unittest

from uhd_wrapper.utils.remote_usrp_error import RemoteUsrpError


def rethrowException_emptyUsrpField(msg: str) -> None:
    try:
        raise Exception(msg)
    except Exception as e:
        raise RemoteUsrpError(str(e))


def rethrowException_setUsrpField(msg: str, usrpName: str) -> None:
    try:
        raise Exception(msg)
    except Exception as e:
        raise RemoteUsrpError(str(e), usrpName)


class TestRemoteUsrpError(unittest.TestCase):
    def test_standardExceptionContainsEmptyUsrpField(self) -> None:
        try:
            rethrowException_emptyUsrpField("foo")
        except RemoteUsrpError as e:
            self.assertEqual(e.usrpName, "")

    def test_msgCreatedWithUsrpExceptionMsg(self) -> None:
        DUMMY_MSG = "foo"
        USRP_NAME = "usrp1"
        try:
            rethrowException_setUsrpField(DUMMY_MSG, USRP_NAME)
        except RemoteUsrpError as e:
            self.assertIn(USRP_NAME, str(e))

    def test_msgContainsMsgOfReraisedException(self) -> None:
        DUMMY_MSG = "foo"
        try:
            rethrowException_setUsrpField(DUMMY_MSG, "usrp1")
        except RemoteUsrpError as e:
            self.assertIn(DUMMY_MSG, str(e))
