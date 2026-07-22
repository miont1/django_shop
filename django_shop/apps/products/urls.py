from typing import List

from django.urls import path

from .views import ProductDetailView, ProductListView

app_name = "products"

urlpatterns: List = [
    path("", ProductListView.as_view(), name="product_list"),
    path("products/", ProductListView.as_view(), name="product_list_alias"),
    path("product/<slug:slug>/", ProductDetailView.as_view(), name="product_detail"),
]
