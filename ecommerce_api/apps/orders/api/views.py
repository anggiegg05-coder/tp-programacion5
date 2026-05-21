from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from django.http import HttpResponse

from apps.orders.models import Order
from apps.orders.utils import generate_invoice

from .serializers import OrderSerializer, OrderCreateSerializer


# 🧾 LISTADO DE ÓRDENES DEL USUARIO
class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related('items__product', 'items__variant')


# 🛒 CREAR ORDEN
class OrderCreateView(generics.CreateAPIView):
    serializer_class = OrderCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # FIX: no pasar user=request.user aquí; el serializer ya lo toma de request
        order = serializer.save()

        return Response(
            OrderSerializer(order, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


# 📦 DETALLE DE ORDEN
class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


# ❌ CANCELAR ORDEN
class OrderCancelView(generics.UpdateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def patch(self, request, *args, **kwargs):
        order = self.get_object()

        if order.status != 'pending':
            return Response(
                {'error': 'Solo podés cancelar órdenes pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = 'cancelled'
        order.save()

        return Response(OrderSerializer(order).data)


# 📄 FACTURA PDF
class InvoiceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        order = Order.objects.get(
            pk=pk,
            user=request.user
        )

        pdf = generate_invoice(order)

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="invoice_{order.id}.pdf"'
        )

        return response