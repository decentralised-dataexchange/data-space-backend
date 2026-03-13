from django.urls import path

from . import views

app_name = "governance"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.dashboard_view, name="dashboard"),
    path("partials/metrics/", views.metric_cards_view, name="metric_cards"),
    path("partials/table/", views.dda_table_view, name="dda_table"),
    path(
        "partials/versions/<str:template_id>/",
        views.dda_versions_view,
        name="dda_versions",
    ),
    path(
        "partials/status/<uuid:dda_id>/",
        views.dda_status_update_view,
        name="dda_status_update",
    ),
]
