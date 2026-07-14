from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from apps.cart.cart import Cart # noqa
from apps.orders.models import Order, OrderItem # noqa
from .forms import OrderForm


def order_create(request):
    cart = Cart(request)

    if not cart:
        return redirect('products:product_list')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                if request.user.is_authenticated:
                    order.user = request.user
                order.total_price = cart.get_total_price()
                order.save()
                for item in cart:
                    if not item['has_enough_stock']:
                        raise ValueError('Not enough stock')
                    OrderItem.objects.create(order=order, product=item['product'], price=item['price'], quantity=item['quantity'])
            cart.clear()
            return redirect('orders:success', order_id=order.id)
    else:
        form = OrderForm()

    return render(request, 'orders/order_create.html', {'cart': cart, 'form': form})


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/order_success.html', {'order': order})

