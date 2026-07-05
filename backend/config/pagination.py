from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from utils.response import success_response


class ElementPlusPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "size"
    max_page_size = 500
    page_query_param = "page"

    def get_paginated_response(self, data):
        return success_response(
            data={
                "total": self.page.paginator.count,
                "items": data,
                "page": self.page.number,
                "size": self.page.paginator.per_page,
            }
        )
