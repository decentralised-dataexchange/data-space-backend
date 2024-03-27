from django.urls import path
from .views import DataSourceView, DataSourceCoverImageView, DataSourceLogoImageView

urlpatterns = [
    path("data-source/", DataSourceView.as_view(), name="data_source"),
    path("data-source/coverimage/",
         DataSourceCoverImageView.as_view(), name="cover_image"),
    path("data-source/logoimage/",
         DataSourceLogoImageView.as_view(), name="logo_image"),
]
