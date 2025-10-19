# shop/views.py
from decimal import Decimal
from typing import Dict, List

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.paginator import Paginator
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .models import Brand, Product


# ----------------------------- Helpers ---------------------------------

def bike_categories() -> List[str]:
    """Canonical list of bike part categories used across the site & uploader."""
    return [
        "Ball Bearings & Plain Bearings",
        "Brakes",
        "Cables & Housings",
        "Cockpit",
        "Drivetrain",
        "Forks",
        "Frames",
        "Hubs & Freewheels",
        "Inner Tubes",
        "Pedals",
        "Power Meters",
        "Quick Releases & Thru Axles",
        "Rear Shock Absorbers",
        "Rims",
        "Saddles",
        "Seat Clamps",
        "Seatposts",
        "Shifting Components",
        "Spokes & Nipples",
        "Tires",
        "Wheels",
    ]


def _cart(request) -> Dict[str, int]:
    """Get or create the session cart. Stored as {product_id(str): qty(int)}."""
    cart = request.session.get("cart")
    if not isinstance(cart, dict):
        cart = {}
        request.session["cart"] = cart
    return cart


def _cart_count(cart: Dict[str, int]) -> int:
    return sum(int(q or 0) for q in cart.values())


def _cart_items(cart: Dict[str, int]):
    """Yield dicts of {product, qty, line_total} for existing product IDs."""
    ids = [int(pid) for pid in cart.keys() if str(pid).isdigit()]
    products = {p.id: p for p in Product.objects.filter(id__in=ids)}
    for pid_str, qty in cart.items():
        try:
            pid = int(pid_str)
        except ValueError:
            continue
        p = products.get(pid)
        if not p:
            continue
        qty = max(int(qty or 0), 0)
        line_total = (p.price or Decimal("0")) * qty
        yield {"product": p, "qty": qty, "line_total": line_total}


def _cart_total(cart: Dict[str, int]) -> Decimal:
    total = Decimal("0")
    for row in _cart_items(cart):
        total += row["line_total"]
    return total.quantize(Decimal("0.01"))


def _is_ajax(request) -> bool:
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


# ----------------------------- Catalog ---------------------------------

def product_list(request):
    """Home/catalog page with optional search & category filter + pagination."""
    qs = Product.objects.all().order_by("-id")

    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(name__icontains=q)

    cat = (request.GET.get("cat") or "").strip()
    if cat:
        qs = qs.filter(category=cat)

    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "products": page_obj,
        "categories": bike_categories(),
        "q": q,
        "active_cat": cat,
        "cart_count": _cart_count(_cart(request)),
    }
    return render(request, "shop/product_list.html", context)


# --- Cart & Checkout helpers and views (drop-in) --------------------------
from decimal import Decimal
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages

from .models import Product

FREE_SHIP = Decimal("200.00")

def _get_cart(request):
    """Get the cart dict from session: {product_id(str): qty(int)}"""
    cart = request.session.get("cart")
    if not isinstance(cart, dict):
        cart = {}
    # normalize bad data
    cart = {str(k): int(v) for k, v in cart.items() if int(v) > 0}
    request.session["cart"] = cart
    return cart

def _cart_summary(request):
    """Build a summary dict used by cart page and checkout."""
    cart = _get_cart(request)

    items = []
    subtotal = Decimal("0.00")

    # bulk fetch products
    if cart:
        products = {str(p.id): p for p in Product.objects.filter(id__in=cart.keys())}
    else:
        products = {}

    for pid, qty in cart.items():
        product = products.get(pid)
        if not product:
            continue
        qty = int(qty)
        line_total = (product.price or Decimal("0")) * qty
        items.append({
            "product": product,
            "qty": qty,
            "line_total": line_total,
        })
        subtotal += line_total

    free_ship_remaining = max(FREE_SHIP - subtotal, Decimal("0.00"))
    shipping = Decimal("0.00")  # change if you want paid shipping
    total = subtotal + shipping

    # expose a lot of commonly used names so existing templates pick it up
    return {
        "items": items,                 # list of dicts with product/qty/line_total
        "cart_items": items,            # alias some templates use
        "subtotal": subtotal,
        "cart_subtotal": subtotal,      # alias
        "cart_total": total,            # alias
        "order_total": total,           # alias for checkout
        "shipping": shipping,
        "free_shipping_threshold": FREE_SHIP,
        "free_shipping_remaining": free_ship_remaining,
        "item_count": sum(i["qty"] for i in items),
    }

def cart_view(request):
    ctx = _cart_summary(request)
    return render(request, "shop/cart.html", ctx)

@require_POST
def cart_update_api(request):
    """
    JSON endpoint to change quantity or remove an item.
    Body: { "product_id": <int>, "action": "inc|dec|set|remove", "qty": <int optional> }
    """
    try:
        data = request.POST or request.json()
    except Exception:
        data = request.POST

    pid = str(data.get("product_id"))
    action = (data.get("action") or "").lower()
    qty = data.get("qty")

    cart = _get_cart(request)

    if action == "remove":
        cart.pop(pid, None)
    elif action in ("inc", "dec", "set"):
        cur = int(cart.get(pid, 0))
        if action == "inc":
            cur += 1
        elif action == "dec":
            cur -= 1
        elif action == "set":
            try:
                cur = int(qty)
            except Exception:
                return HttpResponseBadRequest("qty must be int")
        if cur <= 0:
            cart.pop(pid, None)
        else:
            cart[pid] = cur
    else:
        return HttpResponseBadRequest("bad action")

    request.session["cart"] = cart
    request.session.modified = True
    ctx = _cart_summary(request)

    # convert Decimals for JSON
    def d(x): return f"{x:.2f}"
    return JsonResponse({
        "ok": True,
        "item_count": ctx["item_count"],
        "subtotal": d(ctx["subtotal"]),
        "shipping": d(ctx["shipping"]),
        "total": d(ctx["order_total"]),
        "free_shipping_remaining": d(ctx["free_shipping_remaining"]),
        "lines": [
            {
                "id": i["product"].id,
                "qty": i["qty"],
                "line_total": d(i["line_total"]),
            }
            for i in ctx["items"]
        ],
    })

@require_POST
def cart_remove(request, product_id):
    cart = _get_cart(request)
    cart.pop(str(product_id), None)
    request.session["cart"] = cart
    request.session.modified = True
    return redirect("shop:cart")

def checkout_view(request):
    ctx = _cart_summary(request)
    if request.method == "POST":
        # very simple “payment” simulation
        addr = (request.POST.get("address") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        if not addr or not phone:
            messages.error(request, "Address and phone number are required.")
            return render(request, "shop/checkout.html", ctx, status=400)

        # here you would create an Order; we just clear the cart
        request.session["cart"] = {}
        request.session.modified = True
        return redirect("shop:success")

    return render(request, "shop/checkout.html", ctx)

def success_view(request):
    return render(request, "shop/success.html", {})



# ---------------------------- Auth (simple) -----------------------------

def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("shop:product_list")
    else:
        form = UserCreationForm()
    return render(request, "shop/signup.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("shop:product_list")
    else:
        form = AuthenticationForm()
    return render(request, "shop/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("shop:product_list")


# ------------------------- Drag & Drop Uploader -------------------------

@login_required
def uploader_view(request):
    """
    Page with the drag & drop UI. We pass categories so the <select> can be built.
    """
    return render(request, "shop/uploader.html", {
        "categories": bike_categories(),
    })


@require_POST
@login_required
def uploader_api_create(request):
    """
    Create a Product from one staged row.
    Expects multipart/form-data with: name, brand, category, price, image (file)
    Returns JSON.
    """
    name = (request.POST.get("name") or "").strip() or "New Product"
    brand_name = (request.POST.get("brand") or "").strip()
    category = (request.POST.get("category") or "").strip()
    price_raw = (request.POST.get("price") or "0").strip()
    image_file = request.FILES.get("image")

    if not image_file:
        return JsonResponse({"ok": False, "error": "no_image", "message": "Missing image file."}, status=400)

    # parse price safely
    try:
        price = Decimal(price_raw)
    except Exception:
        price = Decimal("0")

    brand = None
    if brand_name:
        brand, _ = Brand.objects.get_or_create(name=brand_name)

    product = Product.objects.create(
        name=name,
        brand=brand,
        category=category,
        price=price,
        image=image_file,  # saved to MEDIA_ROOT/products/ by ImageField
        image_url="",
    )
    return JsonResponse({"ok": True, "id": product.id, "name": product.name})


@require_http_methods(["POST"])
@login_required
def uploader_api_delete(request, pk: int):
    """
    Delete a single product (and its uploaded image). Returns JSON.
    """
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        raise Http404("Product not found")

    # Only allow staff or the user who uploaded (we don't track owner here),
    # so keep it staff-only for safety in shared environments:
    if not request.user.is_staff:
        # if you want non-staff to cancel their own uploads, remove this check
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    if getattr(product, "image", None):
        product.image.delete(save=False)
    product.delete()
    return JsonResponse({"ok": True})


# --------------------------- Staff: delete item -------------------------

@require_http_methods(["POST"])
@user_passes_test(lambda u: u.is_staff)
def product_delete(request, pk: int):
    """Delete an existing product from the catalog (staff only)."""
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        if _is_ajax(request):
            return JsonResponse({"ok": False, "error": "not_found"}, status=404)
        raise Http404("Product not found")

    if getattr(product, "image", None):
        product.image.delete(save=False)
    product.delete()

    if _is_ajax(request):
        return JsonResponse({"ok": True})
    return redirect("shop:product_list")
