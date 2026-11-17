from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('create/', views.order_create, name='order_create'),
    path('success/<int:order_id>/', views.order_success, name='success'),
    path('cancel/<int:order_id>/', views.order_payment_cancel, name='payment_cancel'),
    path('cancel-order/<int:order_id>/', views.order_cancel, name='order_cancel'),
    path('pay/<int:order_id>/', views.order_payment_retry, name='payment_retry'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
]
