"""
Django Admin configuration for the B2B Connection app.

This module registers the following model with the Django admin interface:
    - B2BConnection: Stores business-to-business connection records that
      represent established relationships between organisations in the
      data space ecosystem.

The model uses basic admin registration without custom configurations,
providing standard CRUD operations through the admin interface.
"""

from django.contrib import admin

from b2b_connection.models import B2BConnection

# Register B2BConnection model for admin interface access.
# B2B connections track the relationships between organisations,
# including connection status, establishment date, and related metadata
# for facilitating secure data exchange between business entities.
admin.site.register(B2BConnection)
