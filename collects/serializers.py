from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers

from users.models import User

from .models import Collect, Payment


class UserShortSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "full_name"]


class PaymentSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = ["id", "amount", "created_at", "user"]


class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "collect", "amount"]

    def validate(self, attrs):
        collect = attrs["collect"]
        if timezone.now() >= collect.deadline:
            raise serializers.ValidationError(
                {"amount": "Сбор уже завершён — платежи не принимаются."}
            )
        if collect.target_amount is not None:
            collected = collect.payments.aggregate(total=Sum("amount"))["total"] or 0
            if collected + attrs["amount"] > collect.target_amount:
                raise serializers.ValidationError(
                    {"amount": "Платёж превысит целевую сумму сбора."}
                )
        return attrs


class CollectSerializer(serializers.ModelSerializer):
    author = UserShortSerializer(read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    collected_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = Collect
        fields = [
            "id",
            "author",
            "title",
            "reason",
            "description",
            "target_amount",
            "collected_amount",
            "cover",
            "deadline",
            "created_at",
            "payments",
        ]
        read_only_fields = ["created_at"]

    def validate_deadline(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Дата завершения должна быть в будущем.")
        return value
