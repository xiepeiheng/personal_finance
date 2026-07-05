from rest_framework.renderers import JSONRenderer

from utils.code_enum import CodeEnum


class UnifiedJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            data = {}

        response = renderer_context.get("response")

        if response and 200 <= response.status_code < 400:
            if isinstance(data, dict) and "success" in data:
                return super().render(data, accepted_media_type, renderer_context)

            if isinstance(data, dict) and "data" in data:
                return super().render(
                    {
                        "success": True,
                        "code": CodeEnum.OK.code,
                        "message": data.get("message", CodeEnum.OK.message),
                        "data": data["data"],
                    },
                    accepted_media_type,
                    renderer_context,
                )

            message = CodeEnum.OK.message
            if isinstance(data, dict) and "message" in data:
                message = data["message"]
                del data["message"]

            data = {
                "success": True,
                "code": CodeEnum.OK.code,
                "message": message,
                "data": data if data else None,
            }

        return super().render(data, accepted_media_type, renderer_context)
