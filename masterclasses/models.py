from django.core.validators import MaxValueValidator
from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator


class MasterClass(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    start_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bucket_list = models.JSONField(default=list)  # Will store list of image URLs
    age_restriction = models.PositiveIntegerField(default=0)
    duration = models.PositiveIntegerField(default=60, help_text="Duration in minutes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Master Class'
        verbose_name_plural = 'Master Classes'

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while MasterClass.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Event(models.Model):
    masterclass = models.ForeignKey(
        MasterClass,
        on_delete=models.CASCADE,
        related_name='events'
    )
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)
    available_seats = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_datetime']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'

    def __str__(self):
        return f"{self.masterclass.title} - {self.start_datetime.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        if not self.end_datetime and self.start_datetime and self.masterclass.duration:
            from datetime import timedelta
            self.end_datetime = self.start_datetime + timedelta(minutes=self.masterclass.duration)
        super().save(*args, **kwargs)

    def is_full(self):
        return self.available_seats <= 0

    def reserve_seat(self):
        if not self.is_full():
            self.available_seats -= 1
            self.save()
            return True
        return False
