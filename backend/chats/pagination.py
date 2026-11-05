from rest_framework.pagination import PageNumberPagination


class MessagePagination(PageNumberPagination):
    # The global page size (5) suits listing cards; a chat screen needs
    # enough history to fill it and scroll before loading more.
    page_size = 30
