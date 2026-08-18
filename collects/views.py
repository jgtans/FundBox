from django.db.models import Sum
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Collect, Payment
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (CollectSerializer, PaymentCreateSerializer,
                          PaymentSerializer)


class CollectViewSet(viewsets.ModelViewSet):
    """
    CRUD сборов (K4, K5, K6).
    Оптимизация: JOIN автора + prefetch ленты + агрегация суммы.
    """

    serializer_class = CollectSerializer
    permission_classes = [IsAuthorOrAdminOrReadOnly]
    filterset_fields = ["reason", "author"]

    def get_queryset(self):
        return (
            Collect.objects.select_related("author")
            .prefetch_related("payments__user")
            .annotate(collected_amount=Sum("payments__amount"))
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PaymentViewSet(viewsets.ModelViewSet):
    """Платежи: чтение всем, создание — авторизованным (донор = текущий пользователь)."""

    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ["collect"]

    def get_queryset(self):
        return Payment.objects.select_related("user", "collect")

    def get_serializer_class(self):
        if self.action == "create":
            return PaymentCreateSerializer
        return PaymentSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
