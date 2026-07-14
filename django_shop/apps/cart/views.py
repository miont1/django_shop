import json
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
    
    try:
        cart.add(product=product, quantity=quantity, override_quantity=override)
    except NotEnoughProductInStock:
        pass
    return redirect('cart:cart_detail')

@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
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

    try:
        cart.add(product=product, quantity=quantity, override_quantity=override)
    except NotEnoughProductInStock:
        return JsonResponse({
            'success': False,
            'error': f'Not enough stock for {product.name}. Max available: {product.stock}'
        }, status=400)

    return JsonResponse({
        'success': True,
        'total_price': float(cart.get_total_price()),
        'total_items': len(cart)
    })

@require_POST
def cart_remove_ajax(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return JsonResponse({
        'success': True,
        'total_price': float(cart.get_total_price()),
        'total_items': len(cart)
    })
