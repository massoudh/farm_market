from django.shortcuts import render, redirect
from django.contrib import messages

from .forms import UserRegistrationForm

from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST


def register(request):

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()

            messages.success(
                request,
                "ثبت‌نام شما با موفقیت انجام شد."
            )

            if user.profile.user_type == "seller":
                messages.info(
                    request,
                    "حساب فروشندگی شما پس از تأیید مدیر سامانه فعال خواهد شد."
                )

            return redirect("register")

    else:
        form = UserRegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form}
    )


def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("home")

    else:
        form = AuthenticationForm(request)

    return render(
        request,
        "accounts/login.html",
        {"form": form}
    )

@login_required
@require_POST
def user_logout(request):
    logout(request)
    return redirect("home")

@login_required
def seller_dashboard(request):
    profile = request.user.profile

    if profile.user_type != "seller":
        return redirect("home")

    return render(
        request,
        "accounts/seller_dashboard.html",
        {
            "profile": profile,
            "is_approved": profile.is_approved,
        }
    )