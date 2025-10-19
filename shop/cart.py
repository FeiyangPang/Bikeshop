# shop/cart.py

from decimal import Decimal
from django.shortcuts import get_object_or_404
from .models import Product

CART_SESSION_KEY = 'cart_v1'

def get_cart(session):
    return session.get(CART_SESSION_KEY, {})

def save_cart(session, cart):
    session[CART_SESSION_KEY] = cart
    session.modified = True

def add_to_cart(session, product_id, qty=1):
    cart = get_cart(session)
    cart[str(product_id)] = cart.get(str(product_id), 0) + qty
    save_cart(session, cart)

def remove_from_cart(session, product_id):
    cart = get_cart(session)
    cart.pop(str(product_id), None)
    save_cart(session, cart)

def set_quantity(session, product_id, qty):
    cart = get_cart(session)
    if qty <= 0:
        cart.pop(str(product_id), None)
    else:
        cart[str(product_id)] = qty
    save_cart(session, cart)

def cart_items(session):
    cart = get_cart(session)
    items = []
    total = Decimal('0.00')
    for pid, qty in cart.items():
        p = get_object_or_404(Product, id=int(pid))
        subtotal = p.price * qty
        total += subtotal
        items.append({'product': p, 'quantity': qty, 'subtotal': subtotal})
    return items, total

def cart_total_qty(session) -> int:
    """Sum of all quantities in the cart (for the badge)."""
    return sum(get_cart(session).values())
