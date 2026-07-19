from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication
from django.shortcuts import get_object_or_404
from apps.products.models import Product # noqa
from ..cart import Cart
from .serializers import CartSerializer, AddUpdateCartItemSerializer

class CartViewSet(viewsets.ViewSet):
    authentication_classes = (SessionAuthentication,)
    permission_classes = (AllowAny,)

    def list(self, request):
        cart = Cart(request)
        serializer = CartSerializer(cart.get_all_items(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        serializer = AddUpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        cart = Cart(request)
        product = get_object_or_404(Product, pk=data['product_id'])
        cart.add(product=product, quantity=data['quantity'])
        return Response(CartSerializer(cart.get_all_items(), many=True).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None, *args, **kwargs):
        quantity = request.data.get('quantity')
        override_quantity = request.data.get('override_quantity')

        serializer = AddUpdateCartItemSerializer(data={'product_id':pk, 'quantity':quantity, 'override_quantity':override_quantity})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        product = get_object_or_404(Product, pk=pk)
        cart = Cart(request)
        cart.add(product=product, quantity=data['quantity'], override_quantity=override_quantity)
        return Response(CartSerializer(cart.get_all_items(), many=True).data, status=status.HTTP_206_PARTIAL_CONTENT)

    def destroy(self, request, pk:str|None=None, *args, **kwargs):
        cart = Cart(request)
        if pk == 'all':
            cart.clear()
            return Response(CartSerializer(cart.get_all_items(), many=True).data)

        product = get_object_or_404(Product, pk=pk)
        cart.remove(product=product)
        return Response(CartSerializer(cart.get_all_items(), many=True).data, status=status.HTTP_200_OK)
