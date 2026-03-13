from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST

from data_disclosure_agreement.models import DataDisclosureAgreementTemplate

LOGIN_URL = "/governance/login/"

# Governance-specific status transitions (admin actions)
GOVERNANCE_STATUS_TRANSITIONS = {
    ("awaitingForApproval", "approved"),
    ("awaitingForApproval", "rejected"),
    ("approved", "listed"),
    ("listed", "unlisted"),
    ("rejected", "awaitingForApproval"),
}


def _get_base_queryset():
    """Return DDA templates: latest versions, excluding archived."""
    return (
        DataDisclosureAgreementTemplate.objects.filter(isLatestVersion=True)
        .exclude(status="archived")
        .select_related("organisationId")
        .order_by("-updatedAt")
    )


def _get_lawful_basis(dda):
    """Extract lawfulBasis from the DDA JSON record."""
    record = dda.dataDisclosureAgreementRecord
    if isinstance(record, dict):
        return record.get("lawfulBasis", "")
    return ""


@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect("governance:dashboard")

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=email, password=password)
        if user is not None and user.is_active:
            login(request, user)
            return redirect("governance:dashboard")
        return render(
            request,
            "governance/login.html",
            {"error": "Invalid email or password.", "email": email},
        )

    return render(request, "governance/login.html")


def logout_view(request):
    logout(request)
    return redirect("governance:login")


@login_required(login_url=LOGIN_URL)
@require_GET
def dashboard_view(request):
    qs = _get_base_queryset()
    current_status = request.GET.get("status", "")

    filtered_qs = qs.filter(status=current_status) if current_status else qs
    paginator = Paginator(filtered_qs, 10)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    # Annotate lawful_basis onto each object
    for dda in page_obj:
        dda.lawful_basis = _get_lawful_basis(dda)

    context = {
        "ddas": page_obj,
        "page_obj": page_obj,
        "current_status": current_status,
        # Metrics
        "total": qs.count(),
        "awaiting": qs.filter(status="awaitingForApproval").count(),
        "listed": qs.filter(status="listed").count(),
        "rejected": qs.filter(status="rejected").count(),
    }
    return render(request, "governance/dashboard.html", context)


@login_required(login_url=LOGIN_URL)
@require_GET
def metric_cards_view(request):
    qs = _get_base_queryset()
    context = {
        "total": qs.count(),
        "awaiting": qs.filter(status="awaitingForApproval").count(),
        "listed": qs.filter(status="listed").count(),
        "rejected": qs.filter(status="rejected").count(),
    }
    return render(request, "governance/partials/metric_cards.html", context)


@login_required(login_url=LOGIN_URL)
@require_GET
def dda_table_view(request):
    qs = _get_base_queryset()
    current_status = request.GET.get("status", "")

    filtered_qs = qs.filter(status=current_status) if current_status else qs
    paginator = Paginator(filtered_qs, 10)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    for dda in page_obj:
        dda.lawful_basis = _get_lawful_basis(dda)

    context = {
        "ddas": page_obj,
        "page_obj": page_obj,
        "current_status": current_status,
    }
    return render(request, "governance/partials/dda_table.html", context)


@login_required(login_url=LOGIN_URL)
@require_GET
def dda_versions_view(request, template_id):
    versions = (
        DataDisclosureAgreementTemplate.objects.filter(templateId=template_id)
        .exclude(status="archived")
        .select_related("organisationId")
        .order_by("-version")
    )
    return render(
        request,
        "governance/partials/dda_version_dropdown.html",
        {"versions": versions},
    )


@login_required(login_url=LOGIN_URL)
@csrf_protect
@require_POST
def dda_status_update_view(request, dda_id):
    new_status = request.POST.get("new_status", "")

    try:
        dda = DataDisclosureAgreementTemplate.objects.get(pk=dda_id)
    except DataDisclosureAgreementTemplate.DoesNotExist:
        return HttpResponse("DDA not found", status=404)

    if (dda.status, new_status) not in GOVERNANCE_STATUS_TRANSITIONS:
        return HttpResponse("Invalid status transition", status=400)

    # When listing: auto-unlist previous versions (same logic as existing API)
    if new_status == "listed":
        existing_ddas = DataDisclosureAgreementTemplate.objects.filter(
            templateId=dda.templateId,
            organisationId=dda.organisationId,
            isLatestVersion=False,
        )
        for existing_dda in existing_ddas:
            if existing_dda.status != "archived":
                existing_dda.status = "unlisted"
            existing_dda.save()

    # Update both model field and JSON record
    dda_record = dda.dataDisclosureAgreementRecord
    dda_record["status"] = new_status
    dda.status = new_status
    dda.dataDisclosureAgreementRecord = dda_record
    dda.save()

    response = HttpResponse(status=204)
    response["HX-Trigger"] = "dda-status-changed"
    return response
