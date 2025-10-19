# shop/views.py
from decimal import Decimal

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils.text import slugify

from .models import Product, Brand
from .cart import add_to_cart, remove_from_cart, set_quantity, cart_items, cart_total_qty
from .forms import CheckoutForm

# Sidebar categories (match these names when creating products)
CATEGORIES = [
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

def product_list(request):
    """Home page: product grid with optional category + text search."""
    qs = Product.objects.all().select_related('brand')

    cat = request.GET.get('cat')
    if cat:
        qs = qs.filter(category=cat)

    q = request.GET.get('q')
    if q:
        qs = qs.filter(name__icontains=q)

    paginator = Paginator(qs, 12)
    page = request.GET.get('page')
    products = paginator.get_page(page)

    return render(
        request,
        'shop/product_list.html',
        {
            'products': products,
            'categories': CATEGORIES,
        }
    )

@require_POST
def add_item(request, product_id):
    qty = int(request.POST.get('qty', 1))
    add_to_cart(request.session, product_id, qty)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'count': cart_total_qty(request.session)})

    return redirect('shop:view_cart')

def view_cart(request):
    items, total = cart_items(request.session)
    return render(request, 'shop/cart.html', {'items': items, 'total': total})

@require_POST
def update_qty(request, product_id):
    qty = int(request.POST.get('qty', 1))
    set_quantity(request.session, product_id, qty)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        items, total = cart_items(request.session)
        sub = "0.00"
        for it in items:
            if it["product"].id == product_id:
                sub = f"{it['subtotal']:.2f}"
                break
        return JsonResponse({
            "ok": True,
            "total": f"{total:.2f}",
            "item_subtotal": sub,
            "count": cart_total_qty(request.session),
        })
    return redirect('shop:view_cart')

@require_POST
def remove_item(request, product_id):
    remove_from_cart(request.session, product_id)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        items, total = cart_items(request.session)
        return JsonResponse({
            "ok": True,
            "total": f"{total:.2f}",
            "count": cart_total_qty(request.session),
        })
    return redirect('shop:view_cart')

# ---------- Checkout flow ----------
def checkout_view(request):
    items, total = cart_items(request.session)
    if not items:
        return redirect('shop:product_list')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            request.session['last_order'] = {
                'total': f"{total:.2f}",
                **form.cleaned_data
            }
            request.session['cart_v1'] = {}
            request.session.modified = True
            return redirect('shop:success')
    else:
        form = CheckoutForm()

    return render(request, 'shop/checkout.html', {'form': form, 'items': items, 'total': total})

def success_view(request):
    order = request.session.get('last_order')
    return render(request, 'shop/success.html', {'order': order})

# ---------- Auth ----------
def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('shop:product_list')
    else:
        form = UserCreationForm()
    return render(request, 'shop/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('shop:product_list')
    else:
        form = AuthenticationForm()
    return render(request, 'shop/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('shop:product_list')

# ---------- Drag & Drop Uploader ----------
from django.contrib.auth.decorators import login_required
from django.urls import reverse

@login_required
def uploader_view(request):
    return render(request, 'shop/uploader.html', {'categories': CATEGORIES})

@require_POST
def uploader_api_create(request):
    """
    Create a product from multipart/form-data.
    Always returns JSON (even on error) so the front-end can show messages.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'auth', 'message': 'Login required'}, status=401)

    name = (request.POST.get('name') or '').strip() or 'New Product'
    brand_name = (request.POST.get('brand') or '').strip()
    category = (request.POST.get('category') or '').strip()
    price_raw = (request.POST.get('price') or '0').strip()
    image_file = request.FILES.get('image')

    # Basic validation
    if not category:
        return JsonResponse({'ok': False, 'error': 'validation', 'message': 'Missing category'}, status=400)
    if not image_file:
        return JsonResponse({'ok': False, 'error': 'validation', 'message': 'Missing image'}, status=400)

    # Ensure a Brand exists (some schemas require brand != null)
    from .models import Brand, Product
    if brand_name:
        brand, _ = Brand.objects.get_or_create(name=brand_name)
    else:
        brand, _ = Brand.objects.get_or_create(name='Unbranded')

    # Normalize price
    from decimal import Decimal, InvalidOperation
    try:
        price = Decimal(price_raw)
    except (InvalidOperation, TypeError):
        price = Decimal('0.00')

    try:
        product = Product.objects.create(
            name=name,
            brand=brand,
            category=category,
            price=price,
            image=image_file,   # saved to MEDIA_ROOT/products/
            image_url=''        # prefer uploaded image
        )
    except Exception as e:
        # Return the exception string so the UI shows something useful
        return JsonResponse({'ok': False, 'error': 'server', 'message': str(e)}, status=500)

    return JsonResponse({'ok': True, 'id': product.id, 'name': product.name})

from django.views.decorators.http import require_http_methods

@require_http_methods(["POST"])
def uploader_api_delete(request, pk):
    """
    Delete a single product by ID (and its uploaded image file).
    Always returns JSON. Requires auth.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'auth', 'message': 'Login required'}, status=401)

    from .models import Product
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'not_found'}, status=404)

    # Delete file on disk if present
    if getattr(product, "image", None):
        product.image.delete(save=False)

    product.delete()
    return JsonResponse({'ok': True})
