from django.urls import path

from . import views

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("checkout/", views.checkout, name="checkout"),
]
