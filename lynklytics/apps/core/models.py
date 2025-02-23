import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Link(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_url = models.URLField(help_text="URL original que se desea acortar")
    short_code = models.CharField(max_length=10, unique=True, help_text="Código único para redireccionamiento")
    created_at = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField(null=True, blank=True, help_text="Fecha de expiración (opcional)")
    user = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='links',
        help_text="Usuario que creó el enlace (si está autenticado)"
    )

    def __str__(self):
        return f"{self.short_code} -> {self.original_url}"

    def is_expired(self):
        if self.expiration_date:
            return timezone.now() > self.expiration_date
        return False


class ClickEvent(models.Model):
    link = models.ForeignKey(Link, on_delete=models.CASCADE, related_name='clicks')
    clicked_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    referrer = models.URLField(null=True, blank=True)

    def __str__(self):
        return f"Click on {self.link.short_code} at {self.clicked_at}"
