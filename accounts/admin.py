from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "user_type",
        "business_name",
        "phone",
        "is_approved",
        "created_at",
    )

    list_filter = (
        "user_type",
        "is_approved",
    )

    search_fields = (
        "user__username",
        "business_name",
        "phone",
    )

    list_editable = (
        "is_approved",
    )
    