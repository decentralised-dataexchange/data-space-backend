def paginate_queryset(queryset, request):
    offset = request.GET.get('offset')
    limit = request.GET.get('limit')

    try:
        offset = int(offset)
    except ValueError:
        offset = 0

    try:
        limit = int(limit)
    except ValueError:
        limit = 10

    total_items = queryset.count()  # Total items in the queryset

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