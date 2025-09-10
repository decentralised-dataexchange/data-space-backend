from django.urls import path
from .views import DataSourceCoverImageView, DataSourceLogoImageView, DataSourcesView, OrganisationsView, OrganisationCoverImageView, OrganisationLogoImageView
from discovery.views import DataMarketPlaceConfigurationView, DataMarketPlaceAuthorizationConfigurationView
from authorization.views import DataMarketPlaceTokenView
from notification.views import DataMarketPlaceNotificationView


urlpatterns = [

     path("data-source/<uuid:dataSourceId>/coverimage/",
          DataSourceCoverImageView.as_view(), name="datasource_coverimage"),
     path("data-source/<uuid:dataSourceId>/logoimage/",
          DataSourceLogoImageView.as_view(), name="datasource_logoimage"),
     path("data-sources/",
          DataSourcesView.as_view(), name="datasources"),
     path(".well-known/data-space-configuration/",DataMarketPlaceConfigurationView.as_view(), name="dataspace_configuration"),
     path(".well-known/oauth-authorization-server/",DataMarketPlaceAuthorizationConfigurationView.as_view(), name="dataspace_authorization_configuration"),
     path('token', DataMarketPlaceTokenView.as_view(), name='token'),
     path("notification",DataMarketPlaceNotificationView.as_view(), name="notification"),
     path("organisation/",
          OrganisationsView.as_view(), name="organisations"),
     path("organisation/<uuid:organisationId>/coverimage/",
          OrganisationCoverImageView.as_view(), name="organisation_coverimage"),
     path("organisation/<uuid:organisationId>/logoimage/",
          OrganisationLogoImageView.as_view(), name="organisation_logoimage"),
]
