from rest_framework.routers import DefaultRouter
from apps.products.api.views import ProductViewSet
from apps.cart.api.views import CartViewSet

api_router = DefaultRouter()

api_router.register('products', ProductViewSet, basename='product_api')
api_router.register('cart', CartViewSet, basename='cart_api')

urlpatterns = api_router.urls