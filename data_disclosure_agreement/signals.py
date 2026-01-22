from typing import Any, Type

from django.db.models.signals import post_save

from data_disclosure_agreement.models import DataDisclosureAgreement


def query_ddas_and_update_is_latest_flag_to_false_for_previous_versions(
    sender: Type[DataDisclosureAgreement],
    instance: DataDisclosureAgreement,
    **kwargs: Any,
) -> None:
    if instance.isLatestVersion:
        ddas = DataDisclosureAgreement.objects.filter(
            templateId=instance.templateId, isLatestVersion=True
        ).exclude(pk=instance.id)
        for dda in ddas:
            dda.isLatestVersion = False
            dda.save()


post_save.connect(
    query_ddas_and_update_is_latest_flag_to_false_for_previous_versions,
    DataDisclosureAgreement,
)
