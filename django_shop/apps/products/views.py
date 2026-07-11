from django.views.generic import ListView, DetailView
from django.db.models import Q, QuerySet, Sum, Avg
from django.db.models.functions import Coalesce
from .models import Product, Review, Category


class ProductListView(ListView):
    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).prefetch_related("categories")

        search_query = self.request.GET.get("q")
        if search_query:
            queryset = queryset.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))

        category_slugs = self.request.GET.getlist("category")
        if category_slugs:
            queryset = queryset.filter(categories__slug__in=category_slugs).distinct()

        price_lte = self.request.GET.get("price_lte")
        if price_lte:
            queryset = queryset.filter(price__lte=price_lte)

        price_gte = self.request.GET.get("price_gte")
        if price_gte:
            queryset = queryset.filter(price__gte=price_gte)

        sort_param = self.request.GET.get("sort")
        if sort_param == "price_asc":
            queryset = queryset.order_by("price")
        elif sort_param == "price_desc":
            queryset = queryset.order_by("-price")
        elif sort_param == "popularity":
            queryset = queryset.annotate(
                total_sales=Coalesce(Sum("orderitem__quantity"), 0)
            ).order_by("-total_sales")
        else:
            queryset = queryset.order_by("-created_at")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["active_categories"] = self.request.GET.getlist("category")
        context["active_sort"] = self.request.GET.get("sort", "")
        context["search_query"] = self.request.GET.get("q", "")
        
        query_params = self.request.GET.copy()
        if "page" in query_params:
            del query_params["page"]
        context["query_string"] = query_params.urlencode()
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"

    def get_queryset(self):
        return Product.objects.filter(is_active=True).prefetch_related("categories")

    def get_context_data(self, **kwargs):
        context = super(ProductDetailView, self).get_context_data(**kwargs)
        product = self.object
        reviews = product.review_set.all().order_by("-created_at")
        context['reviews'] = reviews
        average_rating = reviews.aggregate(Avg("rating"))["rating__avg"]
        context['average_rating'] = round(average_rating, 2) if average_rating else 'No rating'
        return context