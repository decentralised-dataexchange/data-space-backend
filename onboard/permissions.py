from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):

    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):

        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in ('HEAD', 'OPTIONS'):
            return True

        # Write permissions are only allowed to the owner of the snippet.
        return obj.email == request.user.email
