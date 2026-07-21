from django.contrib import admin
from django.db.models import Avg, Sum, Count
from django.db.models.functions import Coalesce
from django.utils.html import format_html

from .models import Category, Product, Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'products_count', 'created_at', 'updated_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(active_products_count=Count('products'))

    @admin.display(description='Active Products', ordering='active_products_count')
    def products_count(self, obj: Category) -> int:
        return getattr(obj, 'active_products_count', 0)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'price',
        'stock',
        'is_active',
        'average_rating_display',
        'total_sales_display',
        'created_at',
    ]
    list_filter = ['is_active', 'categories', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['price', 'stock', 'is_active']
    readonly_fields = ['created_at', 'updated_at', 'average_rating_display', 'total_sales_display']
    filter_horizontal = ['categories']
    actions = ['make_active', 'make_inactive']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            avg_rating=Avg('reviews__rating'),
            total_sold=Coalesce(Sum('orderitem__quantity'), 0)
        )

    @admin.display(description='Avg Rating', ordering='avg_rating')
    def average_rating_display(self, obj: Product) -> str:
        avg = getattr(obj, 'avg_rating', None)
        if avg is not None:
            return format_html('<b style="color: #f59e0b;">★ {}</b>', f'{avg:.1f}')
        return 'No rating'

    @admin.display(description='Total Sales (units)', ordering='total_sold')
    def total_sales_display(self, obj: Product) -> int:
        return getattr(obj, 'total_sold', 0)

    @admin.action(description='Mark selected products as Active')
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} product(s) successfully marked as active.')

    @admin.action(description='Mark selected products as Inactive')
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} product(s) successfully marked as inactive.')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating_stars', 'short_comment', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__name', 'user__email', 'comment']
    readonly_fields = ['created_at']
    raw_id_fields = ['product', 'user']

    @admin.display(description='Rating', ordering='rating')
    def rating_stars(self, obj: Review) -> str:
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color: #f59e0b; font-size: 1.1em;">{}</span> ({})', stars, obj.rating)

    @admin.display(description='Comment')
    def short_comment(self, obj: Review) -> str:
        if len(obj.comment) > 60:
            return obj.comment[:60] + '...'
        return obj.comment