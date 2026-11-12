from django import forms
from .models import Product


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product

        fields = [
            "category",
            "name",
            "price",
            "quantity",
            "description",
            "image",
        ]

        labels = {
            "category": "دسته‌بندی محصول",
            "name": "نام محصول",
            "price": "قیمت (تومان)",
            "quantity": "موجودی",
            "description": "توضیحات محصول",
            "image": "تصویر محصول",
        }

        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

class CheckoutForm(forms.Form):

    customer_name = forms.CharField(
        max_length=200,
        label="نام و نام خانوادگی تحویل‌گیرنده"
    )

    phone = forms.CharField(
        max_length=20,
        label="شماره تلفن"
    )

    address = forms.CharField(
        label="نشانی کامل تحویل",
        widget=forms.Textarea(attrs={"rows": 4})
    )
