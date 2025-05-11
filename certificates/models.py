from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class Certificate(models.Model):
    AMOUNT_CHOICES = [
        (Decimal('1000.00'), '1000 RUB'),
        (Decimal('2000.00'), '2000 RUB'),
        (Decimal('3000.00'), '3000 RUB'),
        (Decimal('5000.00'), '5000 RUB'),
        (Decimal('10000.00'), '10000 RUB'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='certificates'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        choices=[(amount, label) for amount, label in AMOUNT_CHOICES]
    )
    code = models.CharField(max_length=20, unique=True)
    is_used = models.BooleanField(default=False)
    purchase_date = models.DateTimeField(auto_now_add=True)
    used_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-purchase_date']
        verbose_name = 'Certificate'
        verbose_name_plural = 'Certificates'

    def __str__(self):
        return f"Certificate {self.code} - {self.amount} RUB"

    def use_certificate(self):
        if not self.is_used:
            self.is_used = True
            self.used_date = timezone.now()
            self.save()
            return True
        return False
