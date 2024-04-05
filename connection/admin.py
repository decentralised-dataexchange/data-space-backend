from django.contrib import admin
from .models import Connection
from customadminsite.admin import myadminsite

# Register your models here.
myadminsite.register(Connection)