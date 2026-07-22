from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.products.models import Product  # noqa

from ..cart import Cart
from .serializers import AddUpdateCartItemSerializer, CartSerializer


class CartViewSet(viewsets.ViewSet):
    authentication_classes = (SessionAuthentication,)
    permission_classes = (AllowAny,)

    def list(self, request):
        cart = Cart(request)
        serializer = CartSerializer(cart.get_all_items())
        return Response(serializer.data, status=status.HTTP_200_OK)


    @extend_schema(request=AddUpdateCartItemSerializer, responses={200: CartSerializer})
    def create(self, request):
        serializer = AddUpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        cart = Cart(request)
        product = get_object_or_404(Product, pk=data['product_id'])
        cart.add(product=product, quantity=data['quantity'])
        response_data = CartSerializer(cart.get_all_items()).data
        return Response(response_data, status=status.HTTP_201_CREATED)

    @extend_schema(request=AddUpdateCartItemSerializer, responses={200: CartSerializer})
    def partial_update(self, request, pk=None, *args, **kwargs):
        payload = {**request.data, 'product_id': pk}

        serializer = AddUpdateCartItemSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        product = get_object_or_404(Product, pk=pk)
        cart = Cart(request)
        cart.add(product=product, quantity=data['quantity'], override_quantity=payload['override_quantity'])
        response_data = CartSerializer(cart.get_all_items()).data
        return Response(response_data, status=status.HTTP_200_OK)

    @extend_schema(responses={200: CartSerializer},
                   parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.STR,
                description="Product ID to be deleted (`24`), or `all` for a full cart clear.",
            )
        ],)
    def destroy(self, request, pk:str|None=None, *args, **kwargs):
        cart = Cart(request)
        if pk == 'all':
            cart.clear()
            response_data = CartSerializer(cart.get_all_items()).data
            return Response(response_data, status=status.HTTP_200_OK)

        product = get_object_or_404(Product, pk=pk)
        cart.remove(product=product)
        response_data = CartSerializer(cart.get_all_items()).data
        return Response(response_data, status=status.HTTP_200_OK)
