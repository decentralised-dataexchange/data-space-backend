from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
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


SORTABLE_FIELDS = {
    "purpose": "dataDisclosureAgreementRecord__purpose",
    "organisation": "organisationId__name",
    "version": "version",
    "status": "status",
    "updatedAt": "updatedAt",
}


def _get_base_queryset():
    """Return DDA templates: latest versions, excluding archived."""
    return (
        DataDisclosureAgreementTemplate.objects.filter(isLatestVersion=True)
        .exclude(status="archived")
        .select_related("organisationId")
    )


def _apply_search_and_sort(qs, request):
    """Apply search filtering and column sorting from request params."""
    search = request.GET.get("search", "").strip()
    if search:
        qs = qs.filter(
            Q(organisationId__name__icontains=search)
            | Q(dataDisclosureAgreementRecord__purpose__icontains=search)
        )

    sort = request.GET.get("sort", "")
    order = request.GET.get("order", "asc")
    db_field = SORTABLE_FIELDS.get(sort)
    if db_field:
        if order == "desc":
            db_field = f"-{db_field}"
        qs = qs.order_by(db_field)
    else:
        qs = qs.order_by("-updatedAt")

    return qs


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
    search = request.GET.get("search", "").strip()
    sort = request.GET.get("sort", "")
    order = request.GET.get("order", "asc")

    filtered_qs = qs.filter(status=current_status) if current_status else qs
    filtered_qs = _apply_search_and_sort(filtered_qs, request)
    paginator = Paginator(filtered_qs, 10)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    # Annotate lawful_basis onto each object
    for dda in page_obj:
        dda.lawful_basis = _get_lawful_basis(dda)

    context = {
        "ddas": page_obj,
        "page_obj": page_obj,
        "current_status": current_status,
        "search": search,
        "current_sort": sort,
        "current_order": order,
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
    search = request.GET.get("search", "").strip()
    sort = request.GET.get("sort", "")
    order = request.GET.get("order", "asc")

    filtered_qs = qs.filter(status=current_status) if current_status else qs
    filtered_qs = _apply_search_and_sort(filtered_qs, request)
    paginator = Paginator(filtered_qs, 10)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    for dda in page_obj:
        dda.lawful_basis = _get_lawful_basis(dda)

    context = {
        "ddas": page_obj,
        "page_obj": page_obj,
        "current_status": current_status,
        "search": search,
        "current_sort": sort,
        "current_order": order,
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
