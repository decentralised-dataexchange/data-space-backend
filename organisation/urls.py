from django.urls import path, include
from .views import OrganisationView, OrganisationCoverImageView, OrganisationLogoImageView

urlpatterns = [
    path("/", OrganisationView.as_view(), name="organisation"),
    path("/coverimage/",
        OrganisationCoverImageView.as_view(), name="organisation_cover_image"),
    path("/logoimage/",
        OrganisationLogoImageView.as_view(), name="logo_image"),
]