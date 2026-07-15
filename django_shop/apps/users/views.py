from django.contrib import messages
from django.shortcuts import render, redirect

from .forms import CustomUserRegisterForm

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