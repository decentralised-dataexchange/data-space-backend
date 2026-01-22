"""
Data Disclosure Agreement (DDA) Signal Handlers.

This module contains Django signal handlers for the DataDisclosureAgreement model.
It implements version management logic to ensure that only one DDA version is marked
as the latest at any given time for a specific template.

The signal handlers in this module maintain data integrity by automatically updating
the `isLatestVersion` flag across related DDA records when a new version is saved.

Business Logic:
    - Each DDA belongs to a template identified by `templateId`
    - Multiple versions of a DDA can exist for the same template
    - Only one version per template should have `isLatestVersion=True`
    - When a new version is marked as latest, all previous versions must be unmarked
"""

from typing import Any, Type

from django.db.models.signals import post_save

from data_disclosure_agreement.models import DataDisclosureAgreement


def query_ddas_and_update_is_latest_flag_to_false_for_previous_versions(
    sender: Type[DataDisclosureAgreement],
    instance: DataDisclosureAgreement,
    **kwargs: Any,
) -> None:
    """
    Signal handler that ensures only one DDA version is marked as latest per template.

    This function is triggered after a DataDisclosureAgreement instance is saved.
    When a DDA is saved with `isLatestVersion=True`, this handler finds all other
    DDAs with the same `templateId` that are also marked as latest and updates
    them to `isLatestVersion=False`.

    This maintains the invariant that exactly one DDA per template can be the
    latest version at any time.

    Args:
        sender: The model class that sent the signal (DataDisclosureAgreement).
        instance: The actual DDA instance that was just saved.
        **kwargs: Additional keyword arguments passed by the signal, including
                  'created' (bool) and 'raw' (bool).

    Returns:
        None

    Business Rules:
        - Only processes if the saved instance has `isLatestVersion=True`
        - Excludes the current instance from the update to avoid infinite loops
        - Updates each previous version individually to trigger any other signals

    Note:
        The individual saves in the loop may seem inefficient, but they ensure
        that any additional signal handlers or model save logic is properly
        executed for each updated record.
    """
    # Only proceed if the saved instance is marked as the latest version
    if instance.isLatestVersion:
        # Find all DDAs with the same templateId that are currently marked as latest
        # Exclude the current instance to avoid updating it or causing infinite recursion
        ddas = DataDisclosureAgreement.objects.filter(
            templateId=instance.templateId, isLatestVersion=True
        ).exclude(pk=instance.id)

        # Iterate through each previous "latest" version and mark it as not latest
        for dda in ddas:
            dda.isLatestVersion = False
            # Save each DDA individually to ensure model save hooks are triggered
            dda.save()


# Register the signal handler to be called after every DataDisclosureAgreement save
# This connection ensures version management logic runs automatically without
# requiring explicit calls in views or serializers
post_save.connect(
    query_ddas_and_update_is_latest_flag_to_false_for_previous_versions,
    DataDisclosureAgreement,
)
