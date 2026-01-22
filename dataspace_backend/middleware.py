from typing import Callable

from django.http import HttpRequest, HttpResponse
from django.urls import Resolver404, resolve


class NonGetAppendSlashMiddleware:
    """Normalize non-GET URLs missing a trailing slash.

    For non-safe HTTP methods (e.g. POST, PUT, PATCH, DELETE), when a request
    comes in without a trailing slash but the corresponding slash-terminated
    path resolves successfully, this middleware rewrites the request path to
    use the slash version.

    This avoids Django's CommonMiddleware raising a RuntimeError when
    APPEND_SLASH=True and it cannot safely redirect while preserving the
    request body.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Only operate on non-safe methods; GET/HEAD/OPTIONS/TRACE keep
        # Django's default APPEND_SLASH redirect behaviour.
        if request.method not in ("GET", "HEAD", "OPTIONS", "TRACE"):
            path_info = request.path_info or ""

            if path_info:
                if not path_info.endswith("/"):
                    candidate_path = f"{path_info}/"
                else:
                    candidate_path = path_info.rstrip("/")
                    if not candidate_path:
                        candidate_path = None

                if candidate_path:
                    try:
                        resolve(candidate_path)
                    except Resolver404:
                        pass
                    else:
                        request.path_info = candidate_path
                        request.META["PATH_INFO"] = candidate_path

        return self.get_response(request)
