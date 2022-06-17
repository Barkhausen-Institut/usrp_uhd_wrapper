from typing import List


class RemoteUsrpError(RuntimeError):
    def __init__(self, actualUsrpMsg: str, usrpName: str = "") -> None:
        self.actualUsrpMsg = actualUsrpMsg
        self.usrpName = usrpName

        self.msg = self.__createExceptionMsg()
        super().__init__(self.msg)

    def __createExceptionMsg(self) -> str:
        return f"Usrp {self.usrpName}: {self.actualUsrpMsg}"


class MultipleErrors(Exception):
    def __init__(self, errors: List[Exception]) -> None:
        self.errors = errors
        super().__init__(self.errors)

    def __str__(self) -> str:
        return "\n".join([str(e) for e in self.errors])
