from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from django.db.models.deletion import ProtectedError
from django.db.models import Count, Q,  Prefetch
from django.db import transaction

from .models import (
    Product,
    Category,
    CartItem,
    Order,
    OrderItem,
    OrderStatusHistory,
    Notification,
    OrderStatusHistory,
    OrderDeliveryHistory,
)
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .forms import ProductForm, CheckoutForm
from django.db.models import Q
import re


def home(request):

    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "")

    products = Product.objects.all()

    cart = request.session.get("cart", {})
    cart_count = len(cart)

    unread_count = 0
    is_seller = False
    profile = None

    # بررسی کاربر واردشده
    if request.user.is_authenticated and hasattr(request.user, "profile"):

        profile = request.user.profile

        if profile.user_type == "buyer":

            unread_count = Notification.objects.filter(
                recipient=profile,
                is_read=False
            ).count()

        elif profile.user_type == "seller":

            is_seller = True

            # فروشنده فقط محصولات خودش را می‌بیند
            products = products.filter(seller=profile)

    # محاسبه تعداد محصولات دسته‌بندی‌ها
    if is_seller:

        categories = Category.objects.annotate(
            product_count=Count(
                "products",
                filter=Q(products__seller=profile)
            )
        )

    else:

        categories = Category.objects.annotate(
            product_count=Count("products")
        )

    # جست‌وجوی محصولات
    if query:
        products = products.filter(
            name__icontains=query
        )

    # فیلتر دسته‌بندی
    selected_category_name = ""

    if category_id:

        products = products.filter(
            category_id=category_id
        )

        selected_category_obj = Category.objects.filter(
            id=category_id
        ).first()

        if selected_category_obj:
            selected_category_name = selected_category_obj.name

    # اطلاعات ارسالی به قالب
    context = {
        "products": products,
        "categories": categories,
        "query": query,
        "selected_category": category_id,
        "selected_category_name": selected_category_name,
        "cart_count": cart_count,
        "unread_count": unread_count,
        "is_seller": is_seller,
    }

    return render(
        request,
        "products/home.html",
        context
    )

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    context = {
        "product": product
    }

    return render(request, "products/product_detail.html", context)

@require_POST
def add_to_cart(request, product_id):

        # جلوگیری از افزودن محصول به سبد خرید توسط فروشنده
    if request.user.is_authenticated and hasattr(request.user, "profile"):

        profile = request.user.profile

        if profile.user_type == "seller":
            messages.error(
                request,
                "فروشندگان امکان افزودن محصول به سبد خرید را ندارند."
            )
            return redirect("home")
        
    product = get_object_or_404(Product, id=product_id)

    if not request.session.session_key:
        request.session.create()

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (ValueError, TypeError):
        messages.error(
            request,
            "تعداد درخواستی معتبر نیست."
        )
        return redirect("home")

    if quantity < 1:
        messages.error(
            request,
            "تعداد محصول باید حداقل یک عدد باشد."
        )
        return redirect("home")

    cart = request.session.get("cart", {})

    product_id_str = str(product_id)

    try:
        current_quantity = int(cart.get(product_id_str, 0))
    except (ValueError, TypeError):
        current_quantity = 0

    if current_quantity < 0:
        current_quantity = 0

    # بررسی موجودی محصول
    if product.quantity <= 0:

        cart.pop(product_id_str, None)

        request.session["cart"] = cart

        CartItem.objects.filter(
            session_key=request.session.session_key,
            product=product
        ).delete()

        messages.warning(
            request,
            "این محصول در حال حاضر موجود نیست."
        )

        return redirect("home")

    # محاسبه تعداد جدید با توجه به موجودی انبار
    new_quantity = min(
        current_quantity + quantity,
        product.quantity
    )

    cart[product_id_str] = new_quantity

    request.session["cart"] = cart

    CartItem.objects.update_or_create(
        session_key=request.session.session_key,
        product=product,
        defaults={"quantity": new_quantity}
    )

    if new_quantity < current_quantity + quantity:
        messages.warning(
            request,
            f"تعداد محصول به دلیل محدودیت موجودی، به {new_quantity} عدد محدود شد."
        )
    else:
        messages.success(
            request,
            "محصول با موفقیت به سبد خرید اضافه شد."
        )

    return redirect("home")

def cart_view(request):

    # جلوگیری از دسترسی فروشندگان به سبد خرید
    if request.user.is_authenticated and hasattr(request.user, "profile"):

        profile = request.user.profile

        if profile.user_type == "seller":
            messages.error(
                request,
                "بخش سبد خرید مخصوص خریداران است."
            )
            return redirect("home")

    cart = request.session.get("cart", {})

    products = Product.objects.filter(id__in=cart.keys())

    cart_items = []
    total = 0

    for product in products:
        quantity = cart.get(str(product.id), 0)

        if quantity > 0:
            subtotal = product.price * quantity

            cart_items.append({
                "product": product,
                "quantity": quantity,
                "subtotal": subtotal,
            })

            total += subtotal

    context = {
        "cart_items": cart_items,
        "total": total,
    }

    return render(request, "products/cart.html", context)

@login_required
def checkout(request):

    if not hasattr(request.user, "profile"):
        messages.error(
            request,
            "برای ثبت سفارش ابتدا باید پروفایل داشته باشید."
        )
        return redirect("home")

    profile = request.user.profile

    # فقط خریداران اجازه ثبت سفارش دارند
    if profile.user_type != "buyer":
        messages.error(
            request,
            "فقط حساب‌های خریدار امکان ثبت سفارش دارند."
        )
        return redirect("home")

    cart = request.session.get("cart", {})

    if not cart:
        messages.warning(
            request,
            "سبد خرید شما خالی است."
        )
        return redirect("cart")

    # اطلاعات اولیه از پروفایل خریدار
    initial_data = {
        "customer_name": request.user.get_full_name().strip()
                        or request.user.username,
        "phone": profile.phone,
        "address": profile.address,
    }

    if request.method == "POST":
        form = CheckoutForm(request.POST)

        if form.is_valid():

            try:
                with transaction.atomic():

                    products = Product.objects.select_for_update().filter(
                        id__in=cart.keys()
                    )

                    products_by_id = {
                        str(product.id): product
                        for product in products
                    }

                    # بررسی موجود بودن محصولات و موجودی انبار
                    if len(products_by_id) != len(cart):
                        raise ValueError(
                            "بعضی از محصولات سبد خرید دیگر موجود نیستند."
                        )

                    total = 0

                    for product_id, quantity in cart.items():

                        product = products_by_id[product_id]
                        quantity = int(quantity)

                        if quantity <= 0 or quantity > product.quantity:
                            raise ValueError(
                                f"موجودی محصول «{product.name}» کافی نیست."
                            )

                        total += product.price * quantity

                    # ایجاد سفارش
                    order = Order.objects.create(
                        buyer=profile,
                        customer_name=form.cleaned_data["customer_name"],
                        phone=form.cleaned_data["phone"],
                        address=form.cleaned_data["address"],
                        total_amount=total,
                    )

                    # ثبت اقلام سفارش و کاهش موجودی محصولات
                    for product_id, quantity in cart.items():

                        product = products_by_id[product_id]
                        quantity = int(quantity)

                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            product_name=product.name,
                            unit_price=product.price,
                            quantity=quantity,
                        )

                        product.quantity -= quantity
                        product.save(update_fields=["quantity"])

                # پاک کردن سبد خرید پس از ثبت موفق سفارش
                session_key = request.session.session_key

                if session_key:
                    CartItem.objects.filter(
                        session_key=session_key
                    ).delete()

                request.session["cart"] = {}

                messages.success(
                    request,
                    "سفارش شما با موفقیت ثبت شد."
                )

                return redirect("home")

            except (ValueError, TypeError) as error:
                messages.error(request, str(error))
                return redirect("cart")

    else:
        form = CheckoutForm(initial=initial_data)

    return render(
        request,
        "products/checkout.html",
        {"form": form}
    )

@require_POST
def remove_from_cart(request, product_id):

        # جلوگیری از حذف محصولات سبد خرید توسط فروشنده
    if request.user.is_authenticated and hasattr(request.user, "profile"):

        profile = request.user.profile

        if profile.user_type == "seller":
            messages.error(
                request,
                "فروشندگان امکان تغییر سبد خرید را ندارند."
            )
            return redirect("home")
    cart = request.session.get("cart", {})
    product_id_str = str(product_id)

    session_key = request.session.session_key

    if product_id_str in cart:

        del cart[product_id_str]
        request.session["cart"] = cart

        if session_key:
            CartItem.objects.filter(
                session_key=session_key,
                product_id=product_id
            ).delete()

        messages.success(
            request,
            "محصول با موفقیت از سبد خرید حذف شد."
        )

    else:
        messages.warning(
            request,
            "این محصول در سبد خرید شما وجود ندارد."
        )

    return redirect("cart")

@require_POST
def update_cart(request, product_id):

        # جلوگیری از تغییر سبد خرید توسط فروشنده
    if request.user.is_authenticated and hasattr(request.user, "profile"):

        profile = request.user.profile

        if profile.user_type == "seller":
            messages.error(
                request,
                "فروشندگان امکان تغییر سبد خرید را ندارند."
            )
            return redirect("home")
    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get("cart", {})
    product_id_str = str(product_id)

    if product_id_str not in cart:
        messages.warning(
            request,
            "این محصول در سبد خرید شما وجود ندارد."
        )
        return redirect("cart")

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (ValueError, TypeError):
        messages.error(
            request,
            "تعداد واردشده معتبر نیست."
        )
        return redirect("cart")

    if quantity <= 0:
        del cart[product_id_str]

        messages.success(
            request,
            "محصول از سبد خرید حذف شد."
        )

    elif product.quantity <= 0:
        del cart[product_id_str]

        messages.warning(
            request,
            "موجودی این محصول به پایان رسیده و از سبد خرید حذف شد."
        )

    elif quantity > product.quantity:
        cart[product_id_str] = product.quantity

        messages.warning(
            request,
            f"موجودی کافی نیست. تعداد به حداکثر موجودی، یعنی {product.quantity} عدد، محدود شد."
        )

    else:
        cart[product_id_str] = quantity

        messages.success(
            request,
            "تعداد محصول با موفقیت به‌روزرسانی شد."
        )

    request.session["cart"] = cart

    if not request.session.session_key:
        request.session.create()

    if product_id_str in cart:
        CartItem.objects.update_or_create(
            session_key=request.session.session_key,
            product=product,
            defaults={"quantity": cart[product_id_str]}
        )
    else:
        CartItem.objects.filter(
            session_key=request.session.session_key,
            product=product
        ).delete()

    return redirect("cart")

@login_required
def add_product(request):

    if not hasattr(request.user, "profile"):
        messages.error(
            request,
            "برای دسترسی به این بخش ابتدا باید پروفایل داشته باشید."
        )
        return redirect("home")

    profile = request.user.profile

    if profile.user_type != "seller":
        messages.error(
            request,
            "فقط فروشندگان اجازه ثبت محصول دارند."
        )
        return redirect("home")

    if not profile.is_approved:
        messages.error(
            request,
            "حساب فروشندگی شما هنوز تأیید نشده است."
        )
        return redirect("home")

    if request.method == "POST":

        form = ProductForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            product = form.save(commit=False)

            # تعیین مالک محصول از حساب کاربر واردشده
            product.seller = profile

            product.save()

            messages.success(
                request,
                "محصول با موفقیت ثبت شد."
            )

            return redirect("seller_dashboard")

    else:
        form = ProductForm()

    return render(
        request,
        "products/product_form.html",
        {"form": form}
    )

@login_required
def my_products(request):

    if not hasattr(request.user, "profile"):
        messages.error(
            request,
            "برای دسترسی به این بخش ابتدا باید پروفایل داشته باشید."
        )
        return redirect("home")

    profile = request.user.profile

    if profile.user_type != "seller":
        messages.error(
            request,
            "این بخش فقط مخصوص فروشندگان است."
        )
        return redirect("home")

    if not profile.is_approved:
        messages.error(
            request,
            "حساب فروشندگی شما هنوز تأیید نشده است."
        )
        return redirect("home")

    products = Product.objects.filter(
        seller=profile
    ).order_by("-id")

    return render(
        request,
        "products/my_products.html",
        {"products": products}
    )
@login_required
def edit_product(request, product_id):

    if not hasattr(request.user, "profile"):
        messages.error(
            request,
            "برای دسترسی به این بخش ابتدا باید پروفایل داشته باشید."
        )
        return redirect("home")

    profile = request.user.profile

    if profile.user_type != "seller":
        messages.error(
            request,
            "فقط فروشندگان اجازه ویرایش محصولات را دارند."
        )
        return redirect("home")

    if not profile.is_approved:
        messages.error(
            request,
            "حساب فروشندگی شما هنوز تأیید نشده است."
        )
        return redirect("home")

    product = get_object_or_404(
        Product,
        id=product_id,
        seller=profile
    )

    if request.method == "POST":

        form = ProductForm(
            request.POST,
            request.FILES,
            instance=product
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "محصول با موفقیت ویرایش شد."
            )

            return redirect("my_products")

    else:
        form = ProductForm(instance=product)

    return render(
        request,
        "products/product_form.html",
        {
            "form": form,
            "is_edit": True
        }
    )

@login_required
@require_POST
def delete_product(request, product_id):

    if not hasattr(request.user, "profile"):
        messages.error(
            request,
            "برای دسترسی به این بخش ابتدا باید پروفایل داشته باشید."
        )
        return redirect("home")

    profile = request.user.profile

    if profile.user_type != "seller":
        messages.error(
            request,
            "فقط فروشندگان اجازه حذف محصول را دارند."
        )
        return redirect("home")

    if not profile.is_approved:
        messages.error(
            request,
            "حساب فروشندگی شما هنوز تأیید نشده است."
        )
        return redirect("home")

    product = get_object_or_404(
        Product,
        id=product_id,
        seller=profile
    )

    if CartItem.objects.filter(product=product).exists():
        messages.error(
            request,
            "این محصول در سبد خرید مشتریان قرار دارد و فعلاً قابل حذف نیست."
        )
        return redirect("my_products")

    try:
        product.delete()

        messages.success(
            request,
            "محصول با موفقیت حذف شد."
        )

    except ProtectedError:
        messages.error(
            request,
            "این محصول در سفارش‌های ثبت‌شده مشتریان وجود دارد و "
            "برای حفظ سوابق سفارش‌ها قابل حذف نیست."
        )

    return redirect("my_products")

@login_required
def my_orders(request):

    if not hasattr(request.user, "profile"):
        messages.error(
            request,
            "برای مشاهده سفارش‌ها ابتدا باید پروفایل داشته باشید."
        )
        return redirect("home")

    profile = request.user.profile

    # فقط خریداران امکان مشاهده سفارش‌های خود را دارند
    if profile.user_type != "buyer":
        messages.error(
            request,
            "این بخش فقط برای خریداران قابل دسترسی است."
        )
        return redirect("home")

    selected_status = request.GET.get("status", "")
    search_query = request.GET.get("q", "").strip()

    orders = Order.objects.filter(
        buyer=profile
    )

    # فیلتر بر اساس وضعیت سفارش
    valid_statuses = dict(Order.STATUS_CHOICES)

    if selected_status in valid_statuses:
        orders = orders.filter(status=selected_status)
    else:
        selected_status = ""

    # جست‌وجو بر اساس شماره سفارش یا نام محصول
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(items__product_name__icontains=search_query)
        ).distinct()

    orders = orders.order_by("-created_at")

    return render(
        request,
        "products/my_orders.html",
        {
            "orders": orders,
            "status_choices": Order.STATUS_CHOICES,
            "selected_status": selected_status,
            "search_query": search_query,
        }
    )

@login_required
def my_notifications(request):

    if not hasattr(request.user, "profile"):
        messages.error(
            request,
            "برای دسترسی به این بخش ابتدا باید پروفایل داشته باشید."
        )
        return redirect("home")

    profile = request.user.profile

    if profile.user_type != "buyer":
        messages.error(
            request,
            "این بخش فقط برای خریداران قابل دسترسی است."
        )
        return redirect("home")

    notifications = Notification.objects.filter(
        recipient=profile
    ).select_related("order").order_by("-created_at")

    unread_count = notifications.filter(
        is_read=False
    ).count()

    return render(
        request,
        "products/my_notifications.html",
        {
            "notifications": notifications,
            "unread_count": unread_count,
        }
    )

@login_required
@require_POST
def mark_notification_read(request, notification_id):

    if not hasattr(request.user, "profile"):
        messages.error(
            request,
            "برای دسترسی به این بخش ابتدا باید پروفایل داشته باشید."
        )
        return redirect("home")

    profile = request.user.profile

    if profile.user_type != "buyer":
        messages.error(
            request,
            "این بخش فقط برای خریداران قابل دسترسی است."
        )
        return redirect("home")

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=profile
    )

    notification.is_read = True
    notification.save(update_fields=["is_read"])

    messages.success(
        request,
        "اعلان به‌عنوان خوانده‌شده علامت‌گذاری شد."
    )

    return redirect("my_notifications")


@login_required
def order_detail(request, order_number):

    if not hasattr(request.user, "profile"):
        messages.error(
            request,
            "برای دسترسی به این بخش ابتدا باید پروفایل داشته باشید."
        )
        return redirect("home")

    profile = request.user.profile

    # فقط خریداران اجازه مشاهده جزئیات سفارش را دارند
    if profile.user_type != "buyer":
        messages.error(
            request,
            "این بخش فقط برای خریداران قابل دسترسی است."
        )
        return redirect("home")

    order = get_object_or_404(
        Order.objects.prefetch_related(
            "items",
            "status_history",
            "delivery_history",
        ),
        order_number=order_number,
        buyer=profile
    )

    return render(
        request,
        "products/order_detail.html",
        {"order": order}
    )

@login_required
def seller_orders(request):

    # بررسی وجود پروفایل کاربر
    if not hasattr(request.user, "profile"):
        messages.error(
            request,
            "برای دسترسی به این بخش ابتدا باید پروفایل داشته باشید."
        )
        return redirect("home")

    profile = request.user.profile

    # فقط فروشندگان اجازه دسترسی دارند
    if profile.user_type != "seller":
        messages.error(
            request,
            "این بخش فقط برای فروشندگان قابل دسترسی است."
        )
        return redirect("home")

    # فقط اقلام متعلق به همین فروشنده
    seller_items = OrderItem.objects.filter(
        product__seller=profile
    )

    # فقط سفارش‌هایی که شامل محصولات همین فروشنده هستند
    orders = Order.objects.filter(
        items__product__seller=profile
    ).distinct().order_by("-created_at").prefetch_related(
        Prefetch(
            "items",
            queryset=seller_items,
            to_attr="seller_items"
        )
    )

    return render(
        request,
        "products/seller_orders.html",
        {"orders": orders}
    )

@login_required
@require_POST
def update_seller_order_item_status(request, item_id):

    profile = request.user.profile

    if profile.user_type != "seller":
        messages.error(
            request,
            "فقط فروشندگان اجازه تغییر وضعیت را دارند."
        )
        return redirect("home")

    item = get_object_or_404(
        OrderItem,
        id=item_id,
        product__seller=profile
    )

    new_status = request.POST.get("status")

    valid_statuses = dict(OrderItem.ITEM_STATUS_CHOICES)

    if new_status not in valid_statuses:
        messages.error(
            request,
            "وضعیت انتخاب‌شده معتبر نیست."
        )
        return redirect("seller_orders")

    old_item_status = item.status

    item.status = new_status
    item.save(update_fields=["status"])

    order = item.order

    # اعلان اختصاصی تغییر وضعیت محصول
    if old_item_status != new_status:
        Notification.objects.create(
            recipient=order.buyer,
            order=order,
            title=f"تغییر وضعیت محصول: {item.product_name}",
            message=(
                f"وضعیت محصول «{item.product_name}» "
                f"از «{dict(OrderItem.ITEM_STATUS_CHOICES)[old_item_status]}» "
                f"به «{item.get_status_display()}» تغییر کرد."
            ),
        )

    # بررسی ارسال تمام محصولات سفارش
    all_items_shipped = not order.items.exclude(
        status="shipped"
    ).exists()

    if (
        all_items_shipped
        and order.status in ["confirmed", "processing"]
    ):
        old_status = order.status

        order.status = "shipped"
        order.save(update_fields=["status"])

        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_status,
            new_status="shipped",
            changed_by="سیستم",
        )

        Notification.objects.create(
            recipient=order.buyer,
            order=order,
            title="سفارش شما ارسال شد",
            message=(
                "تمام محصولات سفارش شما آماده و ارسال شده‌اند. "
                "وضعیت سفارش به «ارسال شده» تغییر کرد."
            ),
        )

        messages.success(
            request,
            "تمام محصولات ارسال شده‌اند و وضعیت کلی سفارش نیز به‌روزرسانی شد."
        )

    else:
        messages.success(
            request,
            "وضعیت محصول با موفقیت به‌روزرسانی شد."
        )

    return redirect("seller_orders")

@login_required
def edit_order_delivery(request, order_number):

    if not hasattr(request.user, "profile"):
        messages.error(
            request,
            "برای دسترسی به این بخش ابتدا باید پروفایل داشته باشید."
        )
        return redirect("home")

    profile = request.user.profile

    # فقط خریدار اجازه ویرایش سفارش خود را دارد
    if profile.user_type != "buyer":
        messages.error(
            request,
            "فقط خریداران اجازه ویرایش اطلاعات تحویل را دارند."
        )
        return redirect("home")

    order = get_object_or_404(
        Order,
        order_number=order_number,
        buyer=profile
    )

    # امکان ویرایش فقط پیش از ارسال سفارش
    if order.status not in ["pending", "confirmed", "processing"]:
        messages.error(
            request,
            "ویرایش اطلاعات تحویل این سفارش امکان‌پذیر نیست."
        )
        return redirect(
            "order_detail",
            order_number=order.order_number
        )

    if request.method == "POST":

        customer_name = request.POST.get(
            "customer_name", ""
        ).strip()

        phone = request.POST.get(
            "phone", ""
        ).strip()

        address = request.POST.get(
            "address", ""
        ).strip()

        # تبدیل ارقام فارسی و عربی به انگلیسی
        phone = phone.translate(
            str.maketrans(
                "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
                "01234567890123456789"
            )
        )

        # حذف فاصله و خط تیره
        phone = re.sub(r"[\s-]", "", phone)

        if not customer_name or not phone or not address:

            messages.error(
                request,
                "لطفاً تمام اطلاعات تحویل را تکمیل کنید."
            )

        elif not re.fullmatch(r"09\d{9}", phone):

            messages.error(
                request,
                "شماره تلفن معتبر نیست. شماره باید ۱۱ رقم و با 09 شروع شود."
            )

        else:

            # بررسی تغییر اطلاعات
            has_changes = (
                order.customer_name != customer_name or
                order.phone != phone or
                order.address != address
            )

            if has_changes:

                # ثبت تاریخچه اطلاعات قبلی و جدید
                OrderDeliveryHistory.objects.create(
                    order=order,

                    old_customer_name=order.customer_name,
                    new_customer_name=customer_name,

                    old_phone=order.phone,
                    new_phone=phone,

                    old_address=order.address,
                    new_address=address,

                    changed_by=request.user.username,
                )

                # ذخیره اطلاعات جدید سفارش
                order.customer_name = customer_name
                order.phone = phone
                order.address = address

                order.save(
                    update_fields=[
                        "customer_name",
                        "phone",
                        "address",
                    ]
                )

                messages.success(
                    request,
                    "اطلاعات تحویل سفارش با موفقیت ویرایش شد."
                )

            else:

                messages.info(
                    request,
                    "هیچ تغییری در اطلاعات تحویل ایجاد نشده است."
                )

            return redirect(
                "order_detail",
                order_number=order.order_number
            )

    return render(
        request,
        "products/edit_order_delivery.html",
        {"order": order}
    )
