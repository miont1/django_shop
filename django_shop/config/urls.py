from typing import List

from django.contrib import admin
from django.urls import path

urlpatterns: List = [
    path("admin/", admin.site.urls),
]
