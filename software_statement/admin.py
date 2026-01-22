"""
Django Admin configuration for the Software Statement app.

This module registers the following models with the Django admin interface:
    - SoftwareStatement: Stores software statements that describe client
      applications and their metadata for OAuth2/OpenID Connect flows.
    - SoftwareStatementTemplate: Provides reusable templates for generating
      software statements with predefined configurations.

Both models use basic admin registration without custom configurations,
providing standard CRUD operations through the admin interface.
"""

from django.contrib import admin

from software_statement.models import SoftwareStatement, SoftwareStatementTemplate

# Register SoftwareStatement model for admin interface access.
# Software statements contain metadata about client applications including
# redirect URIs, scopes, and other OAuth2/OIDC configuration parameters.
admin.site.register(SoftwareStatement)

# Register SoftwareStatementTemplate model for admin interface access.
# Templates allow administrators to define standard configurations
# that can be reused when creating new software statements.
admin.site.register(SoftwareStatementTemplate)
