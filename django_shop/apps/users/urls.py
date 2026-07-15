from django.urls import path
from django.contrib.auth import views as auth_views
from .views import user_register
from .forms import CustomLoginForm

app_name = 'users'

urlpatterns = [
    path('register/', user_register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html', form_class=CustomLoginForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]