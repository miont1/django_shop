from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, UpdateView

from apps.orders.models import Order  # noqa

from .forms import CustomUserRegisterForm, UserProfileForm


def user_register(request):
    if request.method == 'POST':
        form = CustomUserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            email = form.cleaned_data.get('email')
            messages.success(request, f'Account created for {email}, you can now login')
            return redirect('users:login')
    else:
        form = CustomUserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('products:product_list')

class AccountView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = UserProfileForm
    template_name = 'users/account.html'
    success_url = reverse_lazy("users:profile")
    success_message = "Your profile has been updated successfully!"

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["orders"] = (Order.objects.filter(user=self.request.user)
                             .prefetch_related("items__product").order_by('-created_at'))

        return context