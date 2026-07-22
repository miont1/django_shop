from django import forms

from .models import Review

RATING_CHOICES = [(i, f'{i} ★') for i in range(1, 6)]

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        labels = {
            'rating': 'Rating',
            'comment': 'Comment',
        }
        widgets = {
            'rating': forms.RadioSelect(
                choices=RATING_CHOICES,
                attrs={'class': 'star-rating-input'}
            ),
            'comment': forms.Textarea(
                attrs={
                    'rows': 4,
                    'placeholder': 'Write your comment',
                    'class': 'Input'
                }
            ),

        }