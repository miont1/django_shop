from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView
from django.db.models import Q, Sum, Avg, Max, QuerySet
from django.db.models.functions import Coalesce

from apps.cart.cart import Cart # noqa

from .forms import ReviewForm
from .models import Product, Category
from .services import check_user_for_review_eligible


class ProductListView(ListView):
    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self) -> QuerySet:
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

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["active_categories"] = self.request.GET.getlist("category")
        context["active_sort"] = self.request.GET.get("sort", "")
        context["search_query"] = self.request.GET.get("q", "")
        
        # Calculate dynamic max price from database for range sliders
        max_db_price = Product.objects.filter(is_active=True).aggregate(Max("price"))["price__max"]
        context["max_db_price"] = int(max_db_price) if max_db_price else 100
        context["price_gte"] = self.request.GET.get("price_gte", "")
        context["price_lte"] = self.request.GET.get("price_lte", "")

        # Build query string for pagination links (preserving other filters)
        query_params = self.request.GET.copy()
        if "page" in query_params:
            del query_params["page"]
        context["query_string"] = query_params.urlencode()
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = reverse('users:login')
            current_path = request.path
            return redirect(f"{login_url}?next={current_path}")
        
        self.object = self.get_object()
        form = ReviewForm(request.POST)

        if not check_user_for_review_eligible(request.user, self.object):
            messages.error(request, "You cannot leave a review for this product (for example, you haven't purchased it or have already left a review).")
            return self.render_to_response(self.get_context_data(form=form))
        
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = self.object
            review.save()
            return redirect(self.object.get_absolute_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_queryset(self):
        return Product.objects.filter(is_active=True).prefetch_related("categories", "reviews__user")

    def get_context_data(self, **kwargs):
        context = super(ProductDetailView, self).get_context_data(**kwargs)
        product = self.object
        
        reviews = product.reviews.all().order_by("-created_at")
        context['reviews'] = reviews
        average_rating = reviews.aggregate(Avg("rating"))["rating__avg"]
        context['average_rating'] = round(average_rating, 2) if average_rating else 'No rating'
        
        # Fetch current cart quantity for this product
        cart = Cart(self.request)
        context['current_quantity'] = cart.cart.get(str(product.id), {}).get('quantity', 0)
        
        # Ensure a ReviewForm instance is available in context
        if 'form' not in context:
            context['form'] = ReviewForm()
            
        return context