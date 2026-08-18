from django.contrib import admin

from .models import Collect, Payment


@admin.register(Collect)
class CollectAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "reason", "target_amount", "deadline")
    list_filter = ("reason",)
    search_fields = ("title",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("collect", "user", "amount", "created_at")
    list_filter = ("collect",)
