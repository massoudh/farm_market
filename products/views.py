from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Count
from .models import Product,Category,CartItem
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .forms import ProductForm



def home(request):
    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "")

    products = Product.objects.all()
    cart = request.session.get("cart", {})
    cart_count = len(cart)
    categories = Category.objects.annotate(
        product_count=Count("products")
    )

    if query:
        products = products.filter(name__icontains=query)

    selected_category_name = ""

    if category_id:
        products = products.filter(category_id=category_id)

        selected_category_obj = Category.objects.filter(
            id=category_id
        ).first()

        if selected_category_obj:
            selected_category_name = selected_category_obj.name

    context = {
        "products": products,
        "categories": categories,
        "query": query,
        "selected_category": category_id,
        "selected_category_name": selected_category_name,
        "cart_count": cart_count,
    }

    return render(request, "products/home.html", context)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    context = {
        "product": product
    }

    return render(request, "products/product_detail.html", context)
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if not request.session.session_key:
        request.session.create()
    try:
        quantity = int(request.POST.get("quantity", 1))
    except (ValueError, TypeError):
        quantity = 1

    if quantity < 1:
        quantity = 1

    cart = request.session.get("cart", {})

    product_id_str = str(product_id)
    current_quantity = cart.get(product_id_str, 0)

    if product.quantity > 0:
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
    
    return redirect("home")

def cart_view(request):
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

@require_POST
def remove_from_cart(request, product_id):
    cart = request.session.get("cart", {})
    product_id_str = str(product_id)

    if product_id_str in cart:
        del cart[product_id_str]
        request.session["cart"] = cart

        session_key = request.session.session_key

        if session_key:
            CartItem.objects.filter(
                session_key=session_key,
                product_id=product_id
            ).delete()

        messages.success(
            request,
            "محصول با موفقیت از سبد خرید حذف شد."
        )

    return redirect("cart")
@require_POST
def update_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get("cart", {})
    product_id_str = str(product_id)

    if product_id_str not in cart:
        return redirect("cart")

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (ValueError, TypeError):
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
    profile = request.user.profile

    if profile.user_type != "seller":
        return redirect("home")

    if not profile.is_approved:
        return redirect("seller_dashboard")

    if request.method == "POST":
        form = ProductForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            product = form.save(commit=False)
            product.seller = profile
            product.save()

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
    profile = request.user.profile

    if profile.user_type != "seller":
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
    profile = request.user.profile

    if profile.user_type != "seller":
        return redirect("home")

    if not profile.is_approved:
        return redirect("seller_dashboard")
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
            return redirect("my_products")

    else:
        form = ProductForm(instance=product)

    return render(
        request,
        "products/product_form.html",
        {"form": form, "is_edit": True}
    )

@login_required
def delete_product(request, product_id):
    profile = request.user.profile


    if profile.user_type != "seller":
        return redirect("home")

    if not profile.is_approved:
        return redirect("seller_dashboard")

    product = get_object_or_404(
        Product,
        id=product_id,
        seller=profile
    )

    if request.method != "POST":
        return redirect("my_products")

    if CartItem.objects.filter(product=product).exists():
        messages.error(
            request,
            "این محصول در سبد خرید مشتریان قرار دارد و فعلاً قابل حذف نیست."
        )
        return redirect("my_products")

    product.delete()

    messages.success(
        request,
        "محصول با موفقیت حذف شد."
    )

    return redirect("my_products")
