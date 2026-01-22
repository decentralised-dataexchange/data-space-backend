"""
Django Admin configuration for the Data Disclosure Agreement Record app.

This module registers the following models with the Django admin interface:
    - DataDisclosureAgreementRecord: Stores individual DDA records capturing
      consent agreements between data providers and data consumers.
    - DataDisclosureAgreementRecordHistory: Maintains an audit trail of all
      changes made to DDA records for compliance and traceability purposes.

Both models use basic admin registration without custom configurations,
providing standard CRUD operations through the admin interface.
"""

from django.contrib import admin

from data_disclosure_agreement_record.models import (
    DataDisclosureAgreementRecord,
    DataDisclosureAgreementRecordHistory,
)

# Register DataDisclosureAgreementRecord model for admin interface access.
# This model stores the core DDA record data including agreement details,
# parties involved, and consent status.
admin.site.register(DataDisclosureAgreementRecord)

# Register DataDisclosureAgreementRecordHistory model for admin interface access.
# This model provides historical tracking of DDA record changes,
# enabling audit capabilities and compliance reporting.
admin.site.register(DataDisclosureAgreementRecordHistory)
