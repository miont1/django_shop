from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import user_register, AccountView, user_logout
from .forms import CustomLoginForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm

app_name = 'users'

urlpatterns = [
    path('register/', user_register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html', form_class=CustomLoginForm), name='login'),
    path('logout/', user_logout, name='logout'),
    path('profile/', AccountView.as_view(), name='profile'),
    path(
        'profile/password-change/',
        auth_views.PasswordChangeView.as_view(
            template_name='users/password_change_form.html',
            success_url=reverse_lazy('users:password_change_done'),
            form_class=PasswordChangeForm,
        ),
        name='password_change'
    ),
    path(
        'profile/password-change/done/',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='users/password_change_done.html'
        ),
        name='password_change_done'
    ),
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset_form.html',
             email_template_name='users/password_reset_email.html',
             success_url=reverse_lazy('users:password_reset_done'),
             form_class=PasswordResetForm,
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html',
             success_url=reverse_lazy('users:password_reset_complete'),
             form_class=SetPasswordForm,
         ),
         name='password_reset_confirm'),
    path('password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ),
         name='password_reset_complete'),
]