from django import forms

from .models import Order, OrderItem


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name',  'middle_name', 'last_name', 'email', 'phone', 'address']
        labels = {
            "first_name": "First name",
            "middle_name": "Middle name",
            "last_name": "Last name",
            "email": "Email",
            "phone": "Phone number",
            "address": "Address details (City, post office)",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "Input", "placeholder": "Ivan"}),
            "middle_name": forms.TextInput(attrs={"class": "Input", "placeholder": "Ivanovich"}),
            "last_name": forms.TextInput(attrs={"class": "Input", "placeholder": "Ivanov"}),
            "email": forms.EmailInput(attrs={"class": "Input", "placeholder": "example@mail.com"}),
            "phone": forms.TextInput(attrs={"class": "Input", "placeholder": "+380991234567"}),
            "address": forms.Textarea(attrs={"class": "Textarea", "rows": 3, "placeholder": "Odessa, New Post №1"}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not phone.startswith(('+380', '0')):
            raise forms.ValidationError('Phone number must be ukrainian')
        return phone