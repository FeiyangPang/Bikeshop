from django import forms

class CheckoutForm(forms.Form):
    full_name = forms.CharField(label="Full name (optional)", required=False)
    address   = forms.CharField(label="Address", widget=forms.TextInput(attrs={"class":"form-control"}))
    phone     = forms.CharField(label="Phone number", widget=forms.TextInput(attrs={"class":"form-control"}))
    email     = forms.EmailField(label="Email (optional)", required=False, widget=forms.EmailInput(attrs={"class":"form-control"}))

    # Add bootstrap form-control for all fields that don't define it explicitly
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for k, f in self.fields.items():
            if "class" not in f.widget.attrs:
                f.widget.attrs["class"] = "form-control"
