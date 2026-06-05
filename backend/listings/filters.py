import django_filters
from .models import Listing


class ListingFilter(django_filters.FilterSet):
    breed = django_filters.BaseInFilter(field_name="breed", lookup_expr="in")
    size = django_filters.BaseInFilter(field_name="size", lookup_expr="in")
    color = django_filters.BaseInFilter(field_name="color", lookup_expr="in")
    gender = django_filters.BaseInFilter(field_name="gender", lookup_expr="in")

    class Meta:
        model = Listing
        fields = ["type", "status", "breed", "size", "color", "gender", "user"]
