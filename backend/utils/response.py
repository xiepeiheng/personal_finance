from rest_framework.response import Response

from utils.code_enum import CodeEnum


def success_response(data=None, message: str = None, code: int = None):
    return Response(
        {
            "success": True,
            "code": code or CodeEnum.OK.code,
            "message": message or CodeEnum.OK.message,
            "data": data,
        }
    )


def error_response(
    code: int = None,
    message: str = None,
    http_status: int = None,
    data=None,
):
    code = code or CodeEnum.PARAM_ERROR.code
    http_status = http_status or (200 if code < 1000 else CodeEnum.PARAM_ERROR.code)
    return Response(
        {
            "success": False,
            "code": code,
            "message": message or CodeEnum(code).message
            if code in [c.value[0] for c in CodeEnum]
            else "操作失败",
            "data": data,
        },
        status=http_status,
    )
