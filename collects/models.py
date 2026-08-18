from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone

from users.models import User


class Collect(models.Model):
    """Групповой денежный сбор (K3)."""

    REASON_CHOICES = [
        ("birthday", "День рождения"),
        ("wedding", "Свадьба"),
        ("new_year", "Новый год"),
        ("gift", "Подарок"),
        ("other", "Другое"),
    ]

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="collects",
        verbose_name="Автор сбора",
    )
    title = models.CharField(max_length=200, verbose_name="Название сбора")
    reason = models.CharField(
        max_length=20,
        choices=REASON_CHOICES,
        default="other",
        verbose_name="Повод",
    )
    description = models.TextField(blank=True, verbose_name="Описание")
    target_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name="Целевая сумма (null = бесконечный сбор)",
    )
    cover = models.ImageField(
        upload_to="covers/",
        verbose_name="Обложка",
    )
    deadline = models.DateTimeField(verbose_name="Дата и время завершения")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Групповой сбор"
        verbose_name_plural = "Групповые сборы"

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.deadline and self.deadline <= timezone.now():
            raise ValidationError(
                {"deadline": "Дата завершения должна быть в будущем."}
            )


@receiver(post_delete, sender=Collect)
def delete_cover_from_disk(sender, instance, **kwargs):
    """K4: обложка удаляется с диска при удалении записи из БД."""
    if instance.cover:
        instance.cover.delete(save=False)


class Payment(models.Model):
    """Платёж для сбора (K2)."""

    collect = models.ForeignKey(
        Collect,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Сбор",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Донор",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(1)],
        verbose_name="Сумма",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"

    def __str__(self):
        return f"{self.user} → {self.collect}: {self.amount}"

    def clean(self):
        super().clean()
        if self.collect_id and timezone.now() >= self.collect.deadline:
            raise ValidationError("Сбор уже завершён — платежи не принимаются.")
        if self.collect.target_amount is not None:
            collected = (
                self.collect.payments.exclude(pk=self.pk).aggregate(
                    total=models.Sum("amount")
                )["total"]
                or 0
            )
            if collected + self.amount > self.collect.target_amount:
                raise ValidationError("Платёж превысит целевую сумму сбора.")
