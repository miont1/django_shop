from django.core.exceptions import PermissionDenied
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
            # Store in session so they can view the success page
            placed_orders = request.session.get('placed_orders', [])
            placed_orders.append(order.id)
            request.session['placed_orders'] = placed_orders
            
            return redirect('orders:success', order_id=order.id)
    else:
        form = OrderForm()

    return render(request, 'orders/order_create.html', {'cart': cart, 'form': form})


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    can_view = False
    
    # 1. Check if user is authenticated and is owner or has matching email
    if request.user.is_authenticated:
        if order.user == request.user or order.email == request.user.email:
            can_view = True
            # Associate order with user if it was anonymous
            if order.user is None and order.email == request.user.email:
                order.user = request.user
                order.save(update_fields=['user'])
                
    # 2. Check if the order was just placed in this session (e.g. guest checkout)
    session_orders = request.session.get('placed_orders', [])
    if order_id in session_orders:
        can_view = True
        
    if not can_view:
        raise PermissionDenied("You do not have permission to view this order.")
        
    return render(request, 'orders/order_success.html', {'order': order})

