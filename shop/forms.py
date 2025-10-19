# shop/forms.py
from django import forms

class CheckoutForm(forms.Form):
    full_name = forms.CharField(
        label="Full name (optional)",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    address = forms.CharField(
        label="Address *",
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        required=True,
    )
    phone = forms.CharField(
        label="Phone number *",
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    email = forms.EmailField(
        label="Email (optional)",
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control"})
    )
