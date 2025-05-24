from django.db import models
from django.conf import settings
from masterclasses.models import MasterClass, Event


class Order(models.Model):
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='created'
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    surname = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    patronymic = models.CharField(max_length=100, null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    telegram = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'

    def __str__(self):
        return f"Order {self.id} - {self.user.email}"

    def calculate_total(self):
        total = sum(item.price * item.quantity for item in self.items.all())
        self.total_price = total
        self.save()
        return total

    def mark_as_paid(self):
        if self.status == 'created':
            self.status = 'paid'
            self.save()
            return True
        return False

    def cancel(self):
        if self.status == 'created':
            self.status = 'cancelled'
            self.save()
            return True
        return False


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    masterclass = models.ForeignKey(MasterClass, on_delete=models.CASCADE, null=True, blank=True)
    event = models.ForeignKey('masterclasses.Event', on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_certificate = models.BooleanField(default=False)

    def __str__(self):
        if self.is_certificate:
            return f"Certificate x {self.quantity}"
        return f"{self.masterclass.name} x {self.quantity}"

    def save(self, *args, **kwargs):
        if not self.price and self.masterclass:
            self.price = self.masterclass.final_price if hasattr(self.masterclass, 'final_price') else self.masterclass.start_price
        super().save(*args, **kwargs)
        self.order.calculate_total()


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.email}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True)
    certificate = models.ForeignKey('certificates.Certificate', on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.event:
            return f"Event {self.event.id} x {self.quantity}"
        if self.certificate:
            return f"Certificate {self.certificate.id} x {self.quantity}"
        return f"CartItem x {self.quantity}"
