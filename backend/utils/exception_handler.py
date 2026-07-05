from django.db.models.deletion import ProtectedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from utils.code_enum import CodeEnum
from utils.logger import get_logger

logger = get_logger(__name__)


def custom_exception_handler(exc, context):
    if hasattr(exc, "code"):
        logger.warning(
            f"业务异常: code={exc.code}, message={exc.message}, "
            f"path={context.get('request').path}"
        )
        response = Response(
            {
                "success": False,
                "code": exc.code,
                "message": exc.message,
                "data": exc.data,
            }
        )
        response.status_code = exc.http_status
        return response

    if isinstance(exc, ProtectedError):
        logger.warning(
            f"保护异常: {exc}, path={context.get('request').path}"
        )
        return Response(
            {
                "success": False,
                "code": CodeEnum.PARAM_ERROR.code,
                "message": "该记录下有相关联的子记录，请先清理后再删除",
                "data": None,
            },
            status=400,
        )

    response = exception_handler(exc, context)

    if response is not None:
        error_messages = _extract_error_messages(response.data)
        status_code = response.status_code

        code_map = {
            400: CodeEnum.PARAM_ERROR,
            401: CodeEnum.TOKEN_INVALID,
            403: CodeEnum.PERMISSION_DENIED,
            404: CodeEnum.NOT_FOUND,
            405: CodeEnum.METHOD_NOT_ALLOWED,
        }

        code_enum = code_map.get(status_code, CodeEnum.PARAM_ERROR)

        logger.warning(
            f"框架异常: status={status_code}, message={error_messages}, "
            f"path={context.get('request').path}"
        )

        response.data = {
            "success": False,
            "code": code_enum.code,
            "message": error_messages[0] if error_messages else code_enum.message,
            "data": None,
        }
        return response

    logger.error(
        f"未处理异常: {type(exc).__name__}: {exc}, path={context.get('request').path}"
    )
    return Response(
        {
            "success": False,
            "code": CodeEnum.SERVER_ERROR.code,
            "message": CodeEnum.SERVER_ERROR.message,
            "data": None,
        },
        status=500,
    )


def _extract_error_messages(data):
    messages = []
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                messages.extend(value)
            elif isinstance(value, dict):
                messages.extend(_extract_error_messages(value))
            else:
                messages.append(str(value))
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                messages.extend(_extract_error_messages(item))
            else:
                messages.append(str(item))
    else:
        messages.append(str(data))
    return messages
