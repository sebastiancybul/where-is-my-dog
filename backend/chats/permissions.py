from rest_framework.permissions import BasePermission


class IsConversationMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.memberships.filter(user=request.user).exists()


class IsListingOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if not obj.listing:
            return False
        return obj.listing.user == request.user
