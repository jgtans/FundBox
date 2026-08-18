import base64
import datetime
import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User

from .models import Collect

PNG_1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
    "AAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


class CollectApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user("author", password="pass12345")
        cls.other = User.objects.create_user("other", password="pass12345")

    def _create_collect(self, **overrides):
        self.client.force_authenticate(user=self.author)
        data = {
            "title": "На день рождения",
            "reason": "birthday",
            "description": "Сбор на подарок",
            "target_amount": "1000.00",
            "deadline": (timezone.now() + datetime.timedelta(days=7)).isoformat(),
            "cover": SimpleUploadedFile("cover.png", PNG_1x1, "image/png"),
        }
        data.update(overrides)
        return self.client.post("/api/collects/", data, format="multipart")

    def test_create_collect_authenticated(self):
        response = self._create_collect()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Collect.objects.count(), 1)

    def test_anonymous_can_list_but_not_create(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get("/api/collects/").status_code, 200)
        response = self.client.post("/api/collects/", {"title": "X"})
        self.assertIn(response.status_code, (401, 403))

    def test_non_author_cannot_update(self):
        pk = self._create_collect().data["id"]
        self.client.force_authenticate(user=self.other)
        response = self.client.patch(f"/api/collects/{pk}/", {"title": "Hack"})
        self.assertEqual(response.status_code, 403)

    def test_deadline_in_past_rejected(self):
        past = (timezone.now() - datetime.timedelta(days=1)).isoformat()
        response = self._create_collect(deadline=past)
        self.assertEqual(response.status_code, 400)

    def test_payment_counts_into_collected_amount(self):
        pk = self._create_collect().data["id"]
        self.client.force_authenticate(user=self.other)
        pay = self.client.post("/api/payments/", {"collect": pk, "amount": "250.00"})
        self.assertEqual(pay.status_code, 201)
        detail = self.client.get(f"/api/collects/{pk}/")
        self.assertEqual(str(detail.data["collected_amount"]), "250.00")
        self.assertEqual(len(detail.data["payments"]), 1)

    def test_payment_over_target_rejected(self):
        pk = self._create_collect().data["id"]
        self.client.force_authenticate(user=self.other)
        pay = self.client.post("/api/payments/", {"collect": pk, "amount": "1500.00"})
        self.assertEqual(pay.status_code, 400)

    def test_payment_after_deadline_rejected(self):
        pk = self._create_collect().data["id"]
        Collect.objects.filter(pk=pk).update(
            deadline=timezone.now() - datetime.timedelta(hours=1)
        )
        self.client.force_authenticate(user=self.other)
        pay = self.client.post("/api/payments/", {"collect": pk, "amount": "10.00"})
        self.assertEqual(pay.status_code, 400)

    def test_cover_deleted_from_disk_on_delete(self):
        pk = self._create_collect().data["id"]
        collect = Collect.objects.get(pk=pk)
        path = collect.cover.path
        self.assertTrue(os.path.exists(path))
        collect.delete()
        self.assertFalse(os.path.exists(path))
