from django.core.validators import MaxValueValidator
from django.db import models
from django.utils.text import slugify


class MasterClass(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    age_restriction = models.PositiveIntegerField(default=0)
    discount = models.IntegerField(
        default=0,
        validators=[MaxValueValidator(100)]
    )
    cover_image = models.ImageField(upload_to='masterclass_covers/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Master Class'
        verbose_name_plural = 'Master Classes'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_discounted_price(self):
        if self.discount:
            return self.price * (1 - self.discount / 100)
        return self.price

    def __str__(self):
        return self.title


class Event(models.Model):
    masterclass = models.ForeignKey(
        MasterClass,
        on_delete=models.CASCADE,
        related_name='events'
    )
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    available_seats = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_datetime']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'

    def __str__(self):
        return f"{self.masterclass.title} - {self.start_datetime.strftime('%Y-%m-%d %H:%M')}"

    def is_full(self):
        return self.available_seats <= 0

    def reserve_seat(self):
        if not self.is_full():
            self.available_seats -= 1
            self.save()
            return True
        return False
