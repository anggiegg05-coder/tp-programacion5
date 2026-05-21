from django.shortcuts import render, get_object_or_404
from .models import Product

def home(request):
    products = Product.objects.filter(available=True)[:8]
    return render(request, "home.html", {"products": products})


def product_list(request):
    products = Product.objects.all()
    return render(request, "products/list.html", {"products": products})


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, "products/detail.html", {"product": product})