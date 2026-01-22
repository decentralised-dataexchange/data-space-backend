import os
from typing import Any
from uuid import UUID

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db.models import Model
from django.http import HttpRequest, HttpResponse, JsonResponse
from rest_framework import status

from config.models import ImageModel

DEFAULT_ASSETS_DIR = os.path.join(settings.BASE_DIR, "resources", "assets")


def get_protocol() -> str:
    """Return https:// for prod, http:// otherwise."""
    return "https://" if os.environ.get("ENV") == "prod" else "http://"


def construct_image_url(
    baseurl: str,
    entity_id: str,
    entity_type: str,
    image_type: str,
    is_public_endpoint: bool = False,
) -> str:
    """
    Construct URL for entity images.

    Args:
        baseurl: The base URL (host)
        entity_id: The entity's UUID
        entity_type: "data-source" or "organisation"
        image_type: "coverimage" or "logoimage"
        is_public_endpoint: If True, use "service" prefix; otherwise "config"
    """
    protocol = get_protocol()
    url_prefix = "service" if is_public_endpoint else "config"
    endpoint = f"/{url_prefix}/{entity_type}/{entity_id}/{image_type}/"
    return f"{protocol}{baseurl}{endpoint}"


def construct_cover_image_url(
    baseurl: str, entity_id: str, entity_type: str, is_public_endpoint: bool = False
) -> str:
    """Construct cover image URL for an entity."""
    return construct_image_url(
        baseurl, entity_id, entity_type, "coverimage", is_public_endpoint
    )


def construct_logo_image_url(
    baseurl: str, entity_id: str, entity_type: str, is_public_endpoint: bool = False
) -> str:
    """Construct logo image URL for an entity."""
    return construct_image_url(
        baseurl, entity_id, entity_type, "logoimage", is_public_endpoint
    )


def load_default_image(filename: str) -> UUID:
    """Load a default image from assets and save to ImageModel."""
    image_path = os.path.join(DEFAULT_ASSETS_DIR, filename)
    with open(image_path, "rb") as image_file:
        image = ImageModel(image_data=image_file.read())
        image.save()
        return image.id


def get_image_response(
    image_id: Any, missing_error_message: str
) -> HttpResponse | JsonResponse:
    """Return HTTP response with image data or error."""
    try:
        image = ImageModel.objects.get(pk=image_id)
    except ImageModel.DoesNotExist:
        return JsonResponse(
            {"error": missing_error_message}, status=status.HTTP_400_BAD_REQUEST
        )
    return HttpResponse(image.image_data, content_type="image/jpeg")


def update_entity_image(
    request: HttpRequest,
    entity: Model,
    uploaded_image: UploadedFile | None,
    image_id_attr: str,
    url_attr: str,
    entity_type: str,
) -> JsonResponse:
    """
    Generic image update for any entity (DataSource or Organisation).

    Args:
        request: The HTTP request
        entity: The entity instance (DataSource or Organisation)
        uploaded_image: The uploaded image file
        image_id_attr: Attribute name for image ID (e.g., "coverImageId")
        url_attr: Attribute name for image URL (e.g., "coverImageUrl")
        entity_type: "data-source" or "organisation"
    """
    if not uploaded_image:
        return JsonResponse(
            {"error": "No image file uploaded"}, status=status.HTTP_400_BAD_REQUEST
        )

    image_data = uploaded_image.read()
    image_id = getattr(entity, image_id_attr)

    if image_id is None:
        image = ImageModel(image_data=image_data)
        setattr(entity, image_id_attr, image.id)
    else:
        image = ImageModel.objects.get(pk=image_id)
        image.image_data = image_data

    image.save()

    # Determine the URL builder based on the attribute
    if "cover" in url_attr.lower():
        url_builder = construct_cover_image_url
    else:
        url_builder = construct_logo_image_url

    setattr(
        entity,
        url_attr,
        url_builder(
            baseurl=request.get_host(),
            entity_id=str(entity.id),  # type: ignore[attr-defined]
            entity_type=entity_type,
            is_public_endpoint=True,
        ),
    )
    entity.save()
    return JsonResponse({"message": "Image uploaded successfully"})
