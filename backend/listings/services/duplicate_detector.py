from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance

from ..models import Listing


class DuplicateDetector:

    def __init__(self, radius_km=2):
        self.radius_km = radius_km

    def find_similar_listings(self, listing_data, listing_type):
        """
        MVP: Find exact matches within radius_km radius.

        Args:
            listing_data (dict): Dog characteristics and location
            listing_type (str): 'found' or 'lost' - which type to search for

        Returns:
            QuerySet: Matching listings ordered by distance
        """

        point_data = listing_data["point"]
        lng = point_data.x
        lat = point_data.y
        user_location = Point(lng, lat, srid=4326)

        # Filter by location, status and type
        filtered = (
            Listing.objects.filter(
                status="active",
                type=listing_type,
                locations__is_primary=True,
                locations__point__distance_lte=(
                    user_location,
                    D(km=self.radius_km),
                ),
            )
            .annotate(distance=Distance("locations__point", user_location))
            .order_by("distance")
        )

        # Filter by collar
        has_collar = listing_data["has_collar"]
        if has_collar:
            filtered = filtered.filter(
                has_collar=has_collar,
                collar_color=listing_data["collar_color"],
            )
        else:
            filtered = filtered.filter(
                has_collar=has_collar,
            )

        # Filter by breed and size
        filtered = filtered.filter(
            breed=listing_data["breed"],
            size=listing_data["size"],
        )

        return filtered
