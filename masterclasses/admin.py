from django.contrib import admin
from .models import MasterClass, Event


class EventInline(admin.TabularInline):
    model = Event
    extra = 1


@admin.register(MasterClass)
class MasterClassAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'discount', 'age_restriction', 'created_at')
    list_filter = ('age_restriction', 'discount')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [EventInline]
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('masterclass', 'start_datetime', 'end_datetime', 'available_seats')
    list_filter = ('start_datetime', 'masterclass')
    search_fields = ('masterclass__title',)
    readonly_fields = ('created_at',)
