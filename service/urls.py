from django.urls import path
from .views import DataSourceCoverImageView, DataSourceLogoImageView, DataSourcesView


urlpatterns = [

    path("data-source/<uuid:dataSourceId>/coverimage",
         DataSourceCoverImageView.as_view(), name="datasource_coverimage"),
    path("data-source/<uuid:dataSourceId>/logoimage",
         DataSourceLogoImageView.as_view(), name="datasource_logoimage"),
    path("data-sources/",
         DataSourcesView.as_view(), name="datasources"),
]
