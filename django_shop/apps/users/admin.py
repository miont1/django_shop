from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count, Sum
from django.utils.html import format_html

from .models import User


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    list_display = [
        'email',
        'full_name',
        'phone',
        'city',
        'total_orders_count',
        'total_spent_display',
        'is_staff',
        'is_active',
        'date_joined',
    ]
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name', 'phone', 'city', 'address']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'middle_name', 'last_name', 'phone', 'address', 'city')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'first_name', 'last_name', 'is_staff', 'is_active'),
        }),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            orders_count=Count('orders'),
            total_spent_sum=Sum('orders__total_price')
        )

    @admin.display(description='Name')
    def full_name(self, obj: User) -> str:
        name_parts = [obj.first_name, obj.last_name]
        full = ' '.join(p for p in name_parts if p)
        return full or '-'

    @admin.display(description='Orders', ordering='orders_count')
    def total_orders_count(self, obj: User) -> int:
        return getattr(obj, 'orders_count', 0)

    @admin.display(description='Total Spent', ordering='total_spent_sum')
    def total_spent_display(self, obj: User) -> str:
        spent = getattr(obj, 'total_spent_sum', None)
        if spent:
            return format_html('<b>${}</b>', f'{spent:.2f}')
        return '$0.00'