from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from ..models import Product
from .serializers import ProductSerializer

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_active=True).prefetch_related('categories').order_by('-created_at','id')
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
