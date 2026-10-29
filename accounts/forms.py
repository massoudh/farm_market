from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import UserProfile


class UserRegistrationForm(UserCreationForm):

    first_name = forms.CharField(
        label="نام",
        max_length=150,
        required=True
    )

    last_name = forms.CharField(
        label="نام خانوادگی",
        max_length=150,
        required=True
    )

    user_type = forms.ChoiceField(
        label="نوع حساب کاربری",
        choices=UserProfile.USER_TYPE_CHOICES,
        widget=forms.RadioSelect
    )

    phone = forms.CharField(
        label="شماره تلفن",
        max_length=20,
        required=True
    )

    business_name = forms.CharField(
        label="نام کسب‌وکار یا مزرعه",
        max_length=200,
        required=False
    )

    address = forms.CharField(
        label="نشانی",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False
    )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "user_type",
            "phone",
            "business_name",
            "address",
            "password1",
            "password2",
        ]

        labels = {
            "username": "نام کاربری",
            "password1": "رمز عبور",
            "password2": "تکرار رمز عبور",
        }

    def clean(self):
        cleaned_data = super().clean()

        user_type = cleaned_data.get("user_type")
        business_name = cleaned_data.get("business_name")
        address = cleaned_data.get("address")

        if user_type == "seller":
            if not business_name:
                self.add_error(
                    "business_name",
                    "برای ثبت‌نام به‌عنوان فروشنده، نام کسب‌وکار یا مزرعه الزامی است."
                )

            if not address:
                self.add_error(
                    "address",
                    "برای ثبت‌نام به‌عنوان فروشنده، وارد کردن نشانی الزامی است."
                )

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]

        if commit:
            user.save()

            UserProfile.objects.create(
                user=user,
                user_type=self.cleaned_data["user_type"],
                phone=self.cleaned_data["phone"],
                business_name=self.cleaned_data.get("business_name", ""),
                address=self.cleaned_data.get("address", ""),
                is_approved=False,
            )

        return user
    