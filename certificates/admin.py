from django.contrib import admin
from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('code', 'user', 'amount', 'is_used', 'purchase_date')
    list_filter = ('is_used', 'amount', 'purchase_date')
    search_fields = ('code', 'user__email')
    readonly_fields = ('purchase_date', 'used_date')
