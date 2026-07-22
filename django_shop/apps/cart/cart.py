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

    def add(self, product:Product, quantity:int=1, override_quantity:bool=False) -> None:
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

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        if not products:
            return

        product_map = {str(product.id): product for product in products}

        # Deleting ids that not in DB
        bug_ids = [p_id for p_id in list(self.cart.keys()) if p_id not in product_map]
        if bug_ids:
            for p_id in bug_ids:
                del self.cart[p_id]
            self.save()

        for product_id, item in self.cart.items():
            if product_id in product_map:
                item_copy = item.copy()
                item_copy['product'] = product_map[product_id]
                item_copy['price'] = Decimal(item_copy['price'])
                item_copy['total_price'] = item_copy['price'] * item_copy['quantity']
                item_copy['has_enough_stock'] = item_copy['product'].stock >= item_copy['quantity']
                yield item_copy

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_all_items(self):
        items = []
        total_cart_price = 0
        for item in self:
            product_id = str(item['product'].id)
            product_name = item['product'].name
            quantity = item['quantity']
            price = item['price']
            total_price = item['total_price']
            has_enough_stock = item['has_enough_stock']
            items.append(
                {
                    "product_id": product_id,
                    "product_name": product_name,
                    "quantity": quantity,
                    "price": price,
                    "total_price": total_price,
                    "has_enough_stock": has_enough_stock,
                }
            )
            total_cart_price += item['total_price']

        return {'items': items, 'total_cart_price': total_cart_price}
