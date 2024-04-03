from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from data_disclosure_agreement.models import DataDisclosureAgreement


def query_ddas_and_update_is_latest_flag_to_false_for_previous_versions(
    sender, instance, **kwargs
):
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
