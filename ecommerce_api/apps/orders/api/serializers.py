from rest_framework import serializers

from apps.orders.models import Order, OrderItem
from apps.products.api.serializers import (
    ProductListSerializer,
    ProductVariantSerializer
)
from apps.coupons.models import Coupon
from apps.cart.models import Cart
from apps.cart.api.views import get_or_create_cart   # FIX: import correcto


# =========================
# ORDER ITEM SERIALIZER
# =========================
class OrderItemSerializer(serializers.ModelSerializer):

    product  = ProductListSerializer(read_only=True)
    variant  = ProductVariantSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model  = OrderItem
        fields = [
            'id',
            'product',
            'variant',
            'price',
            'quantity',
            'subtotal'
        ]

    def get_subtotal(self, obj):
        return obj.get_subtotal()


# =========================
# ORDER SERIALIZER (READ)
# =========================
class OrderSerializer(serializers.ModelSerializer):

    items       = OrderItemSerializer(many=True, read_only=True)
    final_total = serializers.SerializerMethodField()
    user        = serializers.StringRelatedField(read_only=True)
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)

    class Meta:
        model  = Order
        fields = [
            'id',
            'user',
            'status',
            'total_price',
            'discount',
            'final_total',
            'coupon_code',
            'address',
            'items',
            'created',
            'updated'
        ]

    def get_final_total(self, obj):
        return obj.get_final_total()


# =========================
# ORDER CREATE SERIALIZER
# =========================
class OrderCreateSerializer(serializers.ModelSerializer):
    """Crear orden desde carrito"""

    class Meta:
        model  = Order
        fields = ['address']
        extra_kwargs = {
            'address': {'required': False, 'allow_blank': True}
        }

    def create(self, validated_data):

        request = self.context['request']
        user = request.user

        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Debes iniciar sesión para comprar")

        # Carrito correcto (usuario o sesión)
        cart = get_or_create_cart(request)

        # Validar carrito
        if not cart.items.exists():
            raise serializers.ValidationError("El carrito está vacío")

        # Total
        total = cart.get_total()

        # Cupón
        discount = 0
        coupon = None
        coupon_id = request.session.get('coupon_id')

        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id, active=True)
                discount = round(total * coupon.discount / 100, 2)
                coupon.used_count += 1
                coupon.save()
            except Coupon.DoesNotExist:
                pass

        # Crear orden
        order = Order.objects.create(
            user=user,
            address=validated_data.get('address', ''),
            total_price=total,
            discount=discount,
            coupon=coupon,
            status='pending'
        )

        # Crear items y descontar stock
        for cart_item in cart.items.all():

            product  = cart_item.product
            variant  = cart_item.variant
            quantity = cart_item.quantity

            if variant:
                if variant.stock < quantity:
                    order.delete()
                    raise serializers.ValidationError(
                        f'Stock insuficiente para {product.name}'
                    )
                variant.stock -= quantity
                variant.save()
            else:
                if product.stock < quantity:
                    order.delete()
                    raise serializers.ValidationError(
                        f'Stock insuficiente para {product.name}'
                    )
                product.stock -= quantity
                product.save()

            OrderItem.objects.create(
                order=order,
                product=product,
                variant=variant,
                price=cart_item.get_unit_price(),
                quantity=quantity
            )

        # Vaciar carrito
        cart.items.all().delete()

        # Limpiar cupón de sesión
        if 'coupon_id' in request.session:
            del request.session['coupon_id']

        return order