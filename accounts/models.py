from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):

    USER_TYPE_CHOICES = [
        ("buyer", "خریدار"),
        ("seller", "تولیدکننده / فروشنده"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="کاربر"
    )

    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default="buyer",
        verbose_name="نوع حساب"
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="شماره تلفن"
    )

    business_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="نام کسب‌وکار یا مزرعه"
    )

    address = models.TextField(
        blank=True,
        verbose_name="نشانی"
    )

    is_approved = models.BooleanField(
        default=False,
        verbose_name="تأیید مدیر"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ثبت‌نام"
    )

    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"

    class Meta:
        verbose_name = "حساب کاربری"
        verbose_name_plural = "حساب‌های کاربری"
        