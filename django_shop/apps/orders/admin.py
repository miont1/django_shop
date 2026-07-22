from django.contrib import admin
from django.db.models import Count, Sum
from django.utils.html import format_html

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ['product']
    readonly_fields = ['item_total_display']

    @admin.display(description='Subtotal ($)')
    def item_total_display(self, obj: OrderItem) -> str:
        if obj.price and obj.quantity:
            subtotal = obj.price * obj.quantity
            return f'${subtotal:.2f}'
        return '$0.00'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'customer_name',
        'email',
        'status',
        'total_price_display',
        'items_count',
        'created_at',
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'address']
    readonly_fields = ['total_price', 'created_at', 'updated_at']
    list_editable = ['status']
    inlines = [OrderItemInline]
    actions = ['mark_as_paid', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']
    ordering = ['-created_at']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(total_quantity=Sum('items__quantity'))

    @admin.display(description='Customer')
    def customer_name(self, obj: Order) -> str:
        return f'{obj.first_name} {obj.last_name}'

    @admin.display(description='Total Amount', ordering='total_price')
    def total_price_display(self, obj: Order) -> str:
        return format_html('<b>${}</b>', f'{obj.total_price:.2f}')

    @admin.display(description='Items Count', ordering='total_quantity')
    def items_count(self, obj: Order) -> int:
        return getattr(obj, 'total_quantity', 0) or 0

    @admin.action(description='Mark selected orders as Paid')
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status=Order.Status.paid)
        self.message_user(request, f'{updated} order(s) updated to Paid.')

    @admin.action(description='Mark selected orders as Shipped')
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status=Order.Status.shipped)
        self.message_user(request, f'{updated} order(s) updated to Shipped.')

    @admin.action(description='Mark selected orders as Delivered')
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status=Order.Status.delivered)
        self.message_user(request, f'{updated} order(s) updated to Delivered.')

    @admin.action(description='Mark selected orders as Cancelled')
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status=Order.Status.cancelled)
        self.message_user(request, f'{updated} order(s) updated to Cancelled.')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'product', 'quantity', 'price']
    list_filter = ['order__status']
    search_fields = ['order__id', 'product__name', 'order__email']
    raw_id_fields = ['order', 'product']