from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Кастомный пользователь проекта FundBox (K1)."""

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
