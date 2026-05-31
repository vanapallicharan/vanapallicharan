from decimal import Decimal

from django.shortcuts import get_object_or_404, redirect, render

from .models import Order, Product


def _cart_items(request):
    cart = request.session.get("cart", {})
    items = []
    total = Decimal("0.00")
    for product_id, quantity in cart.items():
        product = Product.objects.get(pk=product_id)
        line_total = product.price * quantity
        items.append({"product": product, "quantity": quantity, "line_total": line_total})
        total += line_total
    return items, total


def product_list(request):
    products = Product.objects.order_by("category", "name")
    return render(request, "shop/product_list.html", {"products": products})


def add_to_cart(request, product_id):
    get_object_or_404(Product, pk=product_id)
    cart = request.session.get("cart", {})
    key = str(product_id)
    cart[key] = cart.get(key, 0) + 1
    request.session["cart"] = cart
    return redirect("cart")


def cart_view(request):
    items, total = _cart_items(request)
    return render(request, "shop/cart.html", {"items": items, "total": total})


def checkout(request):
    items, total = _cart_items(request)
    if request.method == "POST" and items:
        Order.objects.create(
            customer_name=request.POST["customer_name"],
            email=request.POST["email"],
            address=request.POST["address"],
            items=[
                {"product": item["product"].name, "quantity": item["quantity"]}
                for item in items
            ],
            total=total,
        )
        request.session["cart"] = {}
        return render(request, "shop/order_success.html")
    return render(request, "shop/checkout.html", {"items": items, "total": total})
