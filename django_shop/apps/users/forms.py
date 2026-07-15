from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

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
            if field_name in ['password1', 'password2']:
                self.fields[field_name].widget.attrs.update({"placeholder": "Value"})


class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({"class": "Input"})
            if field_name == 'username':
                self.fields[field_name].widget.attrs.update({"placeholder": "example@email.com"})
            elif field_name == 'password':
                self.fields[field_name].widget.attrs.update({"placeholder": "Value"})