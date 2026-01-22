"""
Django Admin configuration for the Authorization app.

This module handles admin registration for authorization-related models.

Currently, no models are registered in the admin interface because the
authorization app uses Django's built-in User model for token endpoint
authentication. The existing Django admin User management is sufficient
for administering users who authenticate via the token endpoint.

If custom authorization models (e.g., API keys, custom tokens, or permission
grants) are added in the future, they should be registered here.
"""

# No admin models needed for token endpoint using existing users
