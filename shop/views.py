from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST, require_http_methods
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.urls import reverse

from .models import Product, Brand
from .cart import add_to_cart, remove_from_cart, set_quantity, cart_items, cart_total_qty
from .forms import CheckoutForm

# Sidebar categories
CATEGORIES = [
    "Ball Bearings & Plain Bearings","Brakes","Cables & Housings","Cockpit","Drivetrain","Forks","Frames",
    "Hubs & Freewheels","Inner Tubes","Pedals","Power Meters","Quick Releases & Thru Axles",
    "Rear Shock Absorbers","Rims","Saddles","Seat Clamps","Seatposts","Shifting Components",
    "Spokes & Nipples","Tires","Wheels",
]

def product_list(request):
    qs = Product.objects.all().select_related("brand").order_by("-id")
    cat = request.GET.get("cat")
    if cat: qs = qs.filter(category=cat)
    q = request.GET.get("q")
    if q: qs = qs.filter(name__icontains=q)
    page = Paginator(qs, 12).get_page(request.GET.get("page"))
    return render(request, "shop/product_list.html", {"products": page, "categories": CATEGORIES})

@require_POST
def add_item(request, product_id):
    qty = int(request.POST.get("qty", 1))
    add_to_cart(request.session, product_id, qty)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "count": cart_total_qty(request.session)})
    return redirect("shop:view_cart")

def view_cart(request):
    items, total = cart_items(request.session)
    return render(request, "shop/cart.html", {"items": items, "total": total})

@require_POST
def update_qty(request, product_id):
    qty = int(request.POST.get("qty", 1))
    set_quantity(request.session, product_id, qty)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        items, total = cart_items(request.session)
        sub = "0.00"
        for it in items:
            if it["product"].id == product_id: sub = f"{it['subtotal']:.2f}"; break
        return JsonResponse({"ok": True, "total": f"{total:.2f}", "item_subtotal": sub, "count": cart_total_qty(request.session)})
    return redirect("shop:view_cart")

@require_POST
def remove_item(request, product_id):
    remove_from_cart(request.session, product_id)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        items, total = cart_items(request.session)
        return JsonResponse({"ok": True, "total": f"{total:.2f}", "count": cart_total_qty(request.session)})
    return redirect("shop:view_cart")

# ---- Checkout ----
def checkout_view(request):
    items, total = cart_items(request.session)
    if not items: return redirect("shop:product_list")
    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            request.session["last_order"] = {"total": f"{total:.2f}", **form.cleaned_data}
            request.session["cart_v1"] = {}
            request.session.modified = True
            return redirect("shop:success")
    else:
        form = CheckoutForm()
    return render(request, "shop/checkout.html", {"form": form, "items": items, "total": total})

def success_view(request):
    return render(request, "shop/success.html", {"order": request.session.get("last_order")})

# ---- Auth ----
def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(); login(request, user); return redirect("shop:product_list")
    else:
        form = UserCreationForm()
    return render(request, "shop/signup.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user()); return redirect("shop:product_list")
    else:
        form = AuthenticationForm()
    return render(request, "shop/login.html", {"form": form})

def logout_view(request):
    logout(request); return redirect("shop:product_list")

# ---- Uploader ----
@login_required
def uploader_view(request):
    return render(request, "shop/uploader.html", {"categories": CATEGORIES})

@require_POST
def uploader_api_create(request):
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "auth", "login_url": reverse("shop:login")}, status=401)

    name  = (request.POST.get("name") or "").strip() or "New Product"
    bname = (request.POST.get("brand") or "").strip()
    cat   = (request.POST.get("category") or "").strip()
    price_raw = (request.POST.get("price") or "0").strip()
    img   = request.FILES.get("image")

    if not cat:  return JsonResponse({"ok": False, "error": "validation", "message": "Missing category"}, status=400)
    if not img:  return JsonResponse({"ok": False, "error": "validation", "message": "Missing image"}, status=400)

    brand = Brand.objects.get_or_create(name=bname or "Unbranded")[0]
    try: price = Decimal(price_raw)
    except Exception: price = Decimal("0.00")

    try:
        p = Product.objects.create(name=name, brand=brand, category=cat, price=price, image=img, image_url="")
    except Exception as e:
        return JsonResponse({"ok": False, "error": "server", "message": str(e)}, status=500)

    return JsonResponse({"ok": True, "id": p.id, "name": p.name})

@require_http_methods(["POST"])
def uploader_api_delete(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "auth"}, status=401)
    try:
        p = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return JsonResponse({"ok": False, "error": "not_found"}, status=404)
    if getattr(p, "image", None):
        p.image.delete(save=False)
    p.delete()
    return JsonResponse({"ok": True})

# Staff delete from catalog grid
@require_http_methods(["POST"])
@user_passes_test(lambda u: u.is_staff)
def product_delete(request, pk):
    try:
        p = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return JsonResponse({"ok": False, "error": "not_found"}, status=404)
    if getattr(p, "image", None):
        p.image.delete(save=False)
    p.delete()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True})
    return redirect("shop:product_list")
