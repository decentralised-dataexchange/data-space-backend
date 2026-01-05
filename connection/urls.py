from django.urls import path

from connection.views import DISPDeleteConnectionView

urlpatterns = [
    path(
        "/<uuid:connectionId>/",
        DISPDeleteConnectionView.as_view(),
        name="delete_connection",
    ),
]
