from decimal import Decimal

from django.conf import settings
from django.http import HttpRequest

from apps.products.models import Product  # type: ignore[import-not-found]

from .cart_exeptions import NotEnoughProductInStock

class Cart:

    def __init__(self, request: HttpRequest):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)

        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}

        self.cart = cart

    def add(self, product: Product, quantity=1, override_quantity= False) -> None:
        product_id = str(product.id)

        if product_id in self.cart and not override_quantity:
            target_quantity = self.cart[product_id]['quantity'] + quantity
        else:
            target_quantity = quantity

        if target_quantity > product.stock:
            raise NotEnoughProductInStock

        self.cart[product_id] = {
            'quantity': target_quantity,
            'price': str(product.price),
        }

        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, product: Product) -> None:
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def clear(self):
        self.session.pop(settings.CART_SESSION_ID, None)
        self.cart = {}
        self.save()

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart_copy = self.cart.copy()
        for product in products:
            cart_copy[str(product.id)]['product'] = product

        for item in cart_copy.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            item['has_enough_stock'] = item['product'].stock >= item['quantity']
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())