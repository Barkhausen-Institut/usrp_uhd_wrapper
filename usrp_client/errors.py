from typing import List


class RemoteUsrpError(Exception):
    def __init__(self, actualUsrpMsg: str, usrpName: str = "") -> None:
        self.actualUsrpMsg = actualUsrpMsg
        self.usrpName = usrpName

        self.msg = self._createExceptionMsg()
        super().__init__(self.msg)

    def _createExceptionMsg(self) -> str:
        return f"Usrp {self.usrpName}: {self.actualUsrpMsg}"


class MultipleRemoteUsrpErrors(Exception):
    def __init__(self, errors: List[RemoteUsrpError]) -> None:
        self.errors = errors
        self.msg = self._createExceptionMsg()
        super().__init__(self.msg)

    def __str__(self) -> str:
        return self.msg

    def _createExceptionMsg(self) -> str:
        return "\n".join([str(e) for e in self.errors])
