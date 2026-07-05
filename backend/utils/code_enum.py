from enum import Enum


class CodeEnum(Enum):
    """业务错误码枚举"""

    OK = (0, "操作成功")

    SERVER_ERROR = (500, "服务器内部错误")
    PARAM_ERROR = (400, "参数错误")
    NOT_FOUND = (404, "资源不存在")
    METHOD_NOT_ALLOWED = (405, "请求方法不允许")

    TOKEN_EXPIRED = (1001, "Token已过期")
    TOKEN_INVALID = (1002, "Token无效")
    USER_NOT_LOGIN = (1003, "用户未登录")
    USER_DISABLED = (1004, "账号已停用")

    PERMISSION_DENIED = (2001, "没有操作权限")

    LEDGER_NOT_FOUND = (3001, "账本不存在")
    CATEGORY_NOT_FOUND = (3002, "分类不存在")
    TRANSACTION_NOT_FOUND = (3003, "交易记录不存在")

    AMOUNT_ZERO = (4001, "金额不能为零")

    @property
    def code(self) -> int:
        return self.value[0]

    @property
    def message(self) -> str:
        return self.value[1]
