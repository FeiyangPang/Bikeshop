from decimal import Decimal
from .models import Product

CART_KEY = "cart_v1"

def _get(session):
    cart = session.get(CART_KEY, {})
    if not isinstance(cart, dict):
        cart = {}
    return cart

def _save(session, cart):
    session[CART_KEY] = cart
    session.modified = True

def add_to_cart(session, product_id, qty=1):
    cart = _get(session)
    cart[str(product_id)] = cart.get(str(product_id), 0) + int(qty)
    _save(session, cart)

def set_quantity(session, product_id, qty):
    cart = _get(session)
    if int(qty) <= 0:
        cart.pop(str(product_id), None)
    else:
        cart[str(product_id)] = int(qty)
    _save(session, cart)

def remove_from_cart(session, product_id):
    cart = _get(session)
    cart.pop(str(product_id), None)
    _save(session, cart)

def cart_total_qty(session):
    return sum(_get(session).values())

def cart_items(session):
    cart = _get(session)
    ids = [int(i) for i in cart.keys()]
    products = Product.objects.filter(id__in=ids).select_related("brand")
    items = []
    total = Decimal("0.00")
    by_id = {p.id: p for p in products}
    for sid, qty in cart.items():
        pid = int(sid)
        p = by_id.get(pid)
        if not p:
            continue
        sub = p.price * Decimal(qty)
        total += sub
        items.append({"product": p, "qty": qty, "subtotal": sub})
    return items, total
