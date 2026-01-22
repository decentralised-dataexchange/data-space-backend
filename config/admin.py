"""
Django Admin Configuration for Config Module.

This module registers configuration-related models with the Django admin interface.
The ImageModel is used for storing and managing image assets used throughout
the data space platform.

Registered Models:
    - ImageModel: Storage model for image assets and media files
"""

from django.contrib import admin

from .models import ImageModel

# Register ImageModel with default admin configuration
# Provides basic CRUD operations for managing image assets in the platform
admin.site.register(ImageModel)
