from rest_framework import mixins, permissions, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly

from ..models import Product, Review
from ..services import check_user_for_review_eligible
from .serializers import ProductSerializer, ReviewSerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_active=True).prefetch_related('categories').order_by('-created_at','id')
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

class ReviewViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        product_id = self.kwargs.get('product_pk')
        return Review.objects.filter(product__id=product_id).select_related('user').order_by('-created_at','id')

    def get_permissions(self):
        if self.action == 'list':
            return [permissions.AllowAny()]
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def perform_create(self, serializer):
        product = serializer.validated_data.get('product')

        if not check_user_for_review_eligible(self.request.user, product):
            raise PermissionDenied("You cannot leave a review for this product (for example, you haven't purchased it or have already left a review).")

        serializer.save(user=self.request.user)