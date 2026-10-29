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
        