from django.shortcuts import render

def cart_view(request):
    cart = request.session.get("cart", {})

    return render(request, "cart/cart.html", {
        "cart": cart
    })