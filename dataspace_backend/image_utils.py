"""
Image handling utilities for the Data Space Backend application.

This module provides functions for managing images associated with entities
(DataSource and Organisation) in the system, including:
- Protocol-aware URL construction for image endpoints
- Loading default images from filesystem assets
- Retrieving images from the database and returning HTTP responses
- Generic image upload and update operations for entities

Images are stored in the database using the ImageModel, allowing for
centralized storage and easy retrieval without filesystem dependencies
in production environments.
"""

from __future__ import annotations

import io
import os
from typing import Any
from uuid import UUID

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db.models import Model
from django.http import HttpRequest, HttpResponse, JsonResponse
from PIL import Image
from rest_framework import status

from config.models import ImageModel

# Maximum allowed image upload size in bytes (1 MB)
MAX_IMAGE_UPLOAD_SIZE = 1 * 1024 * 1024

# Target dimensions for each image type: (width, height)
IMAGE_DIMENSIONS: dict[str, tuple[int, int]] = {
    "cover": (1500, 500),
    "logo": (400, 400),
}

# Default directory for static image assets (logos, placeholders, etc.)
# These are used when entities don't have custom images uploaded
DEFAULT_ASSETS_DIR = os.path.join(settings.BASE_DIR, "resources", "assets")


def get_protocol() -> str:
    """
    Determine the appropriate HTTP protocol based on environment.

    In production environments, HTTPS is required for security.
    In development/testing environments, HTTP is used for convenience.

    Returns:
        "https://" for production environment, "http://" otherwise.

    Note:
        The environment is determined by the ENV environment variable.
        Only "prod" triggers HTTPS; all other values use HTTP.
    """
    return "https://" if os.environ.get("ENV") == "prod" else "http://"


def construct_image_url(
    baseurl: str,
    entity_id: str,
    entity_type: str,
    image_type: str,
    is_public_endpoint: bool = False,
) -> str:
    """
    Construct a fully-qualified URL for accessing an entity's image.

    This function builds URLs that point to image endpoints for DataSource
    or Organisation entities. The URL structure differs based on whether
    the endpoint is public-facing (service API) or internal (config API).

    Args:
        baseurl: The base URL/hostname (e.g., "api.example.com").
        entity_id: The UUID of the entity as a string.
        entity_type: The type of entity - either "data-source" or "organisation".
        image_type: The type of image - either "coverimage" or "logoimage".
        is_public_endpoint: If True, uses "service" prefix for public API;
                           if False, uses "config" prefix for admin API.

    Returns:
        A fully-qualified URL string for the image endpoint.

    Example:
        >>> construct_image_url("api.example.com", "abc-123", "organisation", "logoimage", True)
        "https://api.example.com/service/organisation/abc-123/logoimage/"
    """
    protocol = get_protocol()
    # Public endpoints use "service" prefix, admin endpoints use "config" prefix
    url_prefix = "service" if is_public_endpoint else "config"
    endpoint = f"/{url_prefix}/{entity_type}/{entity_id}/{image_type}/"
    return f"{protocol}{baseurl}{endpoint}"


def construct_cover_image_url(
    baseurl: str, entity_id: str, entity_type: str, is_public_endpoint: bool = False
) -> str:
    """
    Construct a URL for an entity's cover image.

    Cover images are typically larger banner-style images displayed
    prominently on entity profile pages.

    Args:
        baseurl: The base URL/hostname.
        entity_id: The UUID of the entity as a string.
        entity_type: The type of entity - "data-source" or "organisation".
        is_public_endpoint: If True, uses public service API prefix.

    Returns:
        A fully-qualified URL string for the cover image endpoint.
    """
    return construct_image_url(
        baseurl, entity_id, entity_type, "coverimage", is_public_endpoint
    )


def construct_logo_image_url(
    baseurl: str, entity_id: str, entity_type: str, is_public_endpoint: bool = False
) -> str:
    """
    Construct a URL for an entity's logo image.

    Logo images are typically smaller, square images used for
    identification in listings and headers.

    Args:
        baseurl: The base URL/hostname.
        entity_id: The UUID of the entity as a string.
        entity_type: The type of entity - "data-source" or "organisation".
        is_public_endpoint: If True, uses public service API prefix.

    Returns:
        A fully-qualified URL string for the logo image endpoint.
    """
    return construct_image_url(
        baseurl, entity_id, entity_type, "logoimage", is_public_endpoint
    )


def load_default_image(filename: str) -> UUID:
    """
    Load a default image from the assets directory and save it to the database.

    This function is used during entity creation to assign default placeholder
    images when no custom image is provided. The image file is read from the
    filesystem and stored in the ImageModel for consistent database-backed
    image storage.

    Args:
        filename: The name of the image file in the DEFAULT_ASSETS_DIR
                 (e.g., "default_logo.png").

    Returns:
        The UUID of the newly created ImageModel instance.

    Raises:
        FileNotFoundError: If the specified image file doesn't exist.
        IOError: If there's an error reading the image file.

    Note:
        The image data is stored as binary in the database, not as a
        file path reference.
    """
    image_path = os.path.join(DEFAULT_ASSETS_DIR, filename)
    with open(image_path, "rb") as image_file:
        # Create new ImageModel with binary image data
        image = ImageModel(image_data=image_file.read())
        image.save()
        return image.id


def get_image_response(
    image_id: Any, missing_error_message: str
) -> HttpResponse | JsonResponse:
    """
    Retrieve an image from the database and return it as an HTTP response.

    This function is used by image-serving endpoints to fetch stored images
    and return them with the appropriate content type for browser display.

    Args:
        image_id: The primary key (UUID) of the ImageModel to retrieve.
        missing_error_message: The error message to return if the image
                              is not found in the database.

    Returns:
        HttpResponse: Contains the image binary data with "image/jpeg"
                     content type if the image is found.
        JsonResponse: Contains an error message with 400 status if the
                     image is not found.

    Note:
        All images are served with "image/jpeg" content type regardless
        of the original format. This may need adjustment for PNG/other formats.
    """
    try:
        image = ImageModel.objects.get(pk=image_id)
    except ImageModel.DoesNotExist:
        return JsonResponse(
            {"error": missing_error_message}, status=status.HTTP_400_BAD_REQUEST
        )
    # Return raw image data with JPEG content type
    return HttpResponse(image.image_data, content_type="image/jpeg")


def validate_and_process_image(image_data: bytes, url_attr: str) -> bytes:
    """
    Validate that the uploaded data is a real image, resize it to the
    expected dimensions, and re-encode as JPEG.

    Args:
        image_data: Raw bytes from the upload.
        url_attr: The entity URL attribute name (e.g. "coverImageUrl")
                  used to determine target dimensions.

    Returns:
        Processed JPEG bytes at the correct dimensions.

    Raises:
        ValueError: If the data is not a valid image.
    """
    try:
        img = Image.open(io.BytesIO(image_data))
        img.load()  # force full decode to catch truncated/corrupt files
    except Exception as exc:
        raise ValueError("Upload is not a valid image") from exc

    # Pick target dimensions based on image type
    if "cover" in url_attr.lower():
        target = IMAGE_DIMENSIONS["cover"]
    else:
        target = IMAGE_DIMENSIONS["logo"]

    img = img.resize(target, Image.LANCZOS)
    img = img.convert("RGB")  # ensure compatibility with JPEG

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def update_entity_image(
    request: HttpRequest,
    entity: Model,
    uploaded_image: UploadedFile | None,
    image_id_attr: str,
    url_attr: str,
    entity_type: str,
) -> JsonResponse:
    """
    Update or create an image for an entity (DataSource or Organisation).

    This is a generic function that handles image uploads for any entity type.
    It supports both creating new images (when the entity has no existing image)
    and updating existing images (replacing the binary data in-place).

    The function also updates the entity's image URL attribute to point to
    the public service endpoint for serving the image.

    Args:
        request: The HTTP request object (used to extract the host for URL construction).
        entity: The entity instance (DataSource or Organisation) to update.
        uploaded_image: The uploaded image file from the request, or None.
        image_id_attr: The name of the entity attribute storing the image ID
                      (e.g., "coverImageId" or "logoImageId").
        url_attr: The name of the entity attribute storing the image URL
                 (e.g., "coverImageUrl" or "logoImageUrl").
        entity_type: The type identifier for URL construction
                    ("data-source" or "organisation").

    Returns:
        JsonResponse: Success message with 200 status, or error message
                     with 400 status if no image was uploaded.

    Business Logic:
        1. Validates that an image file was actually uploaded
        2. Reads the binary image data from the uploaded file
        3. If the entity has no existing image (image_id is None):
           - Creates a new ImageModel with the uploaded data
           - Sets the entity's image_id_attr to the new image's ID
        4. If the entity already has an image:
           - Updates the existing ImageModel's binary data in place
           - This preserves the same image ID/URL for caching purposes
        5. Updates the entity's URL attribute with the public endpoint URL
        6. Saves both the image and entity to the database
    """
    # Validate that an image file was provided in the request
    if not uploaded_image:
        return JsonResponse(
            {"error": "No image file uploaded"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Enforce maximum upload size (1 MB)
    if uploaded_image.size and uploaded_image.size > MAX_IMAGE_UPLOAD_SIZE:
        return JsonResponse(
            {"error": "Image file too large. Maximum allowed size is 1 MB."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Read binary data from the uploaded file and validate/process it
    raw_data = uploaded_image.read()
    try:
        image_data = validate_and_process_image(raw_data, url_attr)
    except ValueError:
        return JsonResponse(
            {"error": "Upload is not a valid image"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    image_id = getattr(entity, image_id_attr)

    # Handle new image creation vs. existing image update
    if image_id is None:
        # No existing image - create a new ImageModel
        image = ImageModel(image_data=image_data)
        # Link the new image to the entity
        setattr(entity, image_id_attr, image.id)
    else:
        # Existing image - update the binary data in place
        # This preserves the image ID, allowing cached URLs to remain valid
        image = ImageModel.objects.get(pk=image_id)
        image.image_data = image_data

    # Persist the image to the database
    image.save()

    # Determine the appropriate URL builder based on the attribute name
    # Cover images and logo images use different URL patterns
    if "cover" in url_attr.lower():
        url_builder = construct_cover_image_url
    else:
        url_builder = construct_logo_image_url

    # Update the entity's image URL to point to the public service endpoint
    setattr(
        entity,
        url_attr,
        url_builder(
            baseurl=request.get_host(),
            entity_id=str(entity.id),  # type: ignore[attr-defined]
            entity_type=entity_type,
            is_public_endpoint=True,  # Use public "service" prefix for URL
        ),
    )
    # Save the entity with the updated image reference and URL
    entity.save()
    return JsonResponse({"message": "Image uploaded successfully"})
