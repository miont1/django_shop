from __future__ import annotations
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.conf import settings
from django.utils.text import slugify

User = settings.AUTH_USER_MODEL

class Category(models.Model):
    name: models.CharField[str, str] = models.CharField(max_length=100)
    slug: models.SlugField[str, str] = models.SlugField(max_length=100, unique=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            self.slug = base_slug
            counter = 0
            while Product.objects.filter(slug=self.slug).exists():
                self.slug = f'{base_slug}-{counter}'
                counter += 1
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(models.Model):
    name: models.CharField[str, str] = models.CharField(max_length=100)
    slug: models.CharField[str, str] = models.SlugField(max_length=100, unique=True)
    description: models.TextField[str, str] = models.TextField(blank=True, null=True)
    price: models.DecimalField[float, float] = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)])
    stock: models.PositiveIntegerField[int, int] = models.PositiveIntegerField(default=0)
    categories = models.ManyToManyField(Category, related_name='products')  # type: ignore[var-annotated]
    image = models.ImageField(upload_to='products', blank=True, null=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            self.slug = base_slug
            counter = 0
            while Product.objects.filter(slug=self.slug).exists():
                self.slug = f'{base_slug}-{counter}'
                counter += 1
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # type: ignore[var-annotated]
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # type: ignore[var-annotated]
    rating: models.PositiveIntegerField[int, int] = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment: models.TextField[str, str] = models.TextField()
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)