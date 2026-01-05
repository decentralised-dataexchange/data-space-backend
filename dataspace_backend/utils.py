from django.http import JsonResponse
from rest_framework import status

from config.models import DataSource


def get_model_by_admin_or_400(model, user, error_message: str):
    """Generic helper to get a model instance by admin user."""
    try:
        return model.objects.get(admin=user), None
    except model.DoesNotExist:
        return None, JsonResponse(
            {"error": error_message}, status=status.HTTP_400_BAD_REQUEST
        )


def get_instance_or_400(model, pk, error_message: str):
    """Generic helper to get a model instance by primary key."""
    try:
        return model.objects.get(pk=pk), None
    except model.DoesNotExist:
        return None, JsonResponse(
            {"error": error_message}, status=status.HTTP_400_BAD_REQUEST
        )


def paginate_queryset(queryset, request):
    offset = request.GET.get('offset')
    limit = request.GET.get('limit')

    try:
        offset = int(offset)
    except (ValueError,TypeError):
        offset = 0

    try:
        limit = int(limit)
    except (ValueError,TypeError):
        limit = 10

    # Total items in the queryset
    try:
        total_items = queryset.count()
    except TypeError:
        total_items = len(queryset)

    offset = max(offset, 0)
    limit = max(0, min(limit, 100))  

    queryset = queryset[offset:offset + limit]

    current_page = (offset // limit) + 1

    pagination_data = {
        'currentPage': current_page,
        'totalItems': total_items,
        'totalPages': (total_items + limit - 1) // limit,
        'limit': limit,
        'hasPrevious': offset > 0,
        'hasNext': offset + limit < total_items,
    }

    return queryset, pagination_data


def get_datasource_or_400(user):
    """Get DataSource by admin user or return 400 error."""
    return get_model_by_admin_or_400(DataSource, user, "Data source not found")


def get_organisation_or_400(user):
    """Get Organisation by admin user or return 400 error."""
    from organisation.models import Organisation
    return get_model_by_admin_or_400(Organisation, user, "Organisation not found")
