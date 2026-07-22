from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from django.urls import path, include
from apps.products.api.views import ProductViewSet, ReviewViewSet
from apps.cart.api.views import CartViewSet

api_router = DefaultRouter()

api_router.register('products', ProductViewSet, basename='product_api')
api_router.register('cart', CartViewSet, basename='cart_api')

products_router = routers.NestedSimpleRouter(api_router, r'products', lookup='product')
products_router.register('reviews', ReviewViewSet, basename='product_reviews_api')

urlpatterns = [
    path('', include(api_router.urls)),
    path('', include(products_router.urls)),
]