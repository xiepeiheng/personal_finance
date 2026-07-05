from utils.code_enum import CodeEnum


class BusinessException(Exception):
    def __init__(
        self,
        code: int = None,
        message: str = None,
        http_status: int = 200,
        data=None,
    ):
        self.code = code or CodeEnum.PARAM_ERROR.code
        self.message = message or CodeEnum.PARAM_ERROR.message
        self.http_status = http_status
        self.data = data
        super().__init__(self.message)

    def __str__(self):
        return f"[{self.code}] {self.message}"
