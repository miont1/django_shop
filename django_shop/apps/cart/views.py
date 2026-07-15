import json
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from apps.products.models import Product
from .cart import Cart
from .cart_exeptions import NotEnoughProductInStock

def cart_detail(request):
    cart = Cart(request)
    # Check if there are any stock issues in the cart
    has_stock_issues = False
    for item in cart:
        if not item['has_enough_stock']:
            has_stock_issues = True
            break
    return render(request, 'cart/cart.html', {
        'cart': cart,
        'has_stock_issues': has_stock_issues
    })

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    override = request.POST.get('override', 'False') == 'True'
    
    product_id_str = str(product.id)
    current_qty = cart.cart.get(product_id_str, {}).get('quantity', 0)
    target_qty = quantity if override else (current_qty + quantity)
    
    try:
        cart.add(product=product, quantity=quantity, override_quantity=override)
        if current_qty == 0:
            messages.success(request, f'"{product.name}" was successfully added to your cart.')
        elif target_qty > current_qty:
            messages.success(request, f'"{product.name}" quantity increased.')
        else:
            messages.success(request, f'Removed 1 unit of "{product.name}" from your cart.')
    except NotEnoughProductInStock:
        messages.error(request, f'Sorry, there is not enough stock for "{product.name}".')
    return redirect('cart:cart_detail')

@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.success(request, f'"{product.name}" was removed from your cart.')
    return redirect('cart:cart_detail')

@require_POST
def cart_add_ajax(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        override = data.get('override', False)
    except (json.JSONDecodeError, ValueError, TypeError):
        quantity = 1
        override = False

    product_id_str = str(product.id)
    current_qty = cart.cart.get(product_id_str, {}).get('quantity', 0)
    target_qty = quantity if override else (current_qty + quantity)

    try:
        cart.add(product=product, quantity=quantity, override_quantity=override)
        if current_qty == 0:
            msg = f'"{product.name}" was successfully added to your cart.'
        elif target_qty > current_qty:
            msg = f'"{product.name}" quantity increased.'
        else:
            msg = f'Removed 1 unit of "{product.name}" from your cart.'
    except NotEnoughProductInStock:
        err_msg = f'Not enough stock for {product.name}. Max available: {product.stock}'
        return JsonResponse({
            'success': False,
            'error': err_msg
        }, status=400)

    return JsonResponse({
        'success': True,
        'message': msg,
        'total_price': float(cart.get_total_price()),
        'total_items': len(cart)
    })

@require_POST
def cart_remove_ajax(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    msg = f'"{product.name}" was removed from your cart.'
    return JsonResponse({
        'success': True,
        'message': msg,
        'total_price': float(cart.get_total_price()),
        'total_items': len(cart)
    })
