from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm,
    PasswordChangeForm as AuthPasswordChangeForm,
    PasswordResetForm as AuthPasswordResetForm,
    SetPasswordForm as AuthSetPasswordForm,
)

User = get_user_model()

class CustomUserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'Input', 'placeholder': 'example@email.com'}),
        label='Email Address'
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({"class": "Input"})
            if field_name == 'password1':
                self.fields[field_name].widget.attrs.update({"placeholder": "Password"})
            elif field_name == 'password2':
                self.fields[field_name].widget.attrs.update({"placeholder": "Confirm Password"})


class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({"class": "Input"})
            if field_name == 'username':
                self.fields[field_name].widget.attrs.update({"placeholder": "example@email.com"})
            elif field_name == 'password':
                self.fields[field_name].widget.attrs.update({"placeholder": "Password"})

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "middle_name" , "last_name", "email", "phone", "address", "city"]

        widgets = {
            "first_name": forms.TextInput(attrs={"class": "Input", "placeholder": "First Name"}),
            "middle_name": forms.TextInput(attrs={"class": "Input", "placeholder": "Middle Name"}),
            "last_name": forms.TextInput(attrs={"class": "Input", "placeholder": "Last Name"}),
            "email": forms.EmailInput(attrs={"class": "Input", "placeholder": "example@email.com"}),
            "phone": forms.TextInput(attrs={"class": "Input", "placeholder": "Phone number"}),
            "address": forms.TextInput(attrs={"class": "Input", "placeholder": "Shipping address"}),
            "city": forms.TextInput(attrs={"class": "Input", "placeholder": "City"}),
        }

class PasswordChangeForm(AuthPasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "old_password": "Old Password",
            "new_password1": "New Password",
            "new_password2": "Confirm New Password"
        }
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                "class": "Input",
                "placeholder": placeholders.get(field_name, "Value")
            })


class PasswordResetForm(AuthPasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                "class": "Input",
                "placeholder": "example@email.com"
            })


class SetPasswordForm(AuthSetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "new_password1": "New Password",
            "new_password2": "Confirm New Password"
        }
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                "class": "Input",
                "placeholder": placeholders.get(field_name, "Value")
            })
