from django.contrib import admin
from django.urls import path, include
from .views import UserList, UserDetail, CreateUserView
from django.views.decorators.csrf import csrf_exempt


urlpatterns = [
        path('/',csrf_exempt(UserList.as_view())),
        path('/register/',csrf_exempt(CreateUserView.as_view())),
        path('/<int:pk>/',csrf_exempt(UserDetail.as_view())),
]
