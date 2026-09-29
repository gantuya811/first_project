"""
MERRIGE ERP - Нэгдсэн хуудаслалт (Pagination)
Бүх жагсаалт харуулах API (бараа, захиалга, тайлан гэх мэт) энэ классыг
ашиглана. Хариултын бүтэц нь API STANDARD-ийн success envelope-тэй яг таарна:
{"success": true, "message": "Амжилттай", "data": {...}}
"""

from collections import OrderedDict

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 200
    page_query_param = "page"

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("success", True),
                    ("message", "Амжилттай"),
                    (
                        "data",
                        OrderedDict(
                            [
                                ("count", self.page.paginator.count),
                                ("total_pages", self.page.paginator.num_pages),
                                ("current_page", self.page.number),
                                ("next", self.get_next_link()),
                                ("previous", self.get_previous_link()),
                                ("results", data),
                            ]
                        ),
                    ),
                ]
            )
        )
