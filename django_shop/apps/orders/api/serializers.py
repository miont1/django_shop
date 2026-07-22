from django.core.validators import validate_email
from rest_framework import serializers

from ...cart.cart import Cart
from ..models import Order
from ..services import make_order


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'first_name', 'middle_name', 'last_name', 'email', 'phone', 'address', 'payment_method', 'status', 'total_price', 'created_at']
        read_only_fields = ['id', 'status', 'total_price', 'created_at']

    def validate_phone(self, value):
        phone = value
        if phone and not phone.startswith(('+380', '0')):
            raise serializers.ValidationError('Phone number must be ukrainian')
        return value

    def validate_email(self, value):
        email = value
        validate_email(email)
        return value

    def create(self, validated_data):
        request = self.context['request']
        cart = Cart(request)

        try:
            return make_order(user=request.user, order_data=validated_data, cart=cart)
        except ValueError as e:
            raise serializers.ValidationError({'detail': str(e)})