from rest_framework import serializers

from apps.products.models import Product # noqa

class CartItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    product_name = serializers.CharField(read_only=True)
    quantity = serializers.IntegerField(min_value=1, default=1)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

class CartSerializer(serializers.Serializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_cart_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

class AddUpdateCartItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    override_quantity = serializers.BooleanField(default=False)

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid product id")
        return value