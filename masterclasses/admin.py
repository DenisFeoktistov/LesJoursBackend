from django.contrib import admin
from .models import MasterClass, Event


class EventInline(admin.TabularInline):
    model = Event
    extra = 1


@admin.register(MasterClass)
class MasterClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_price', 'final_price', 'age_restriction', 'duration', 'created_at')
    list_filter = ('age_restriction', 'duration')
    search_fields = ('name', 'short_description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [EventInline]
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('masterclass', 'start_datetime', 'end_datetime', 'available_seats')
    list_filter = ('start_datetime', 'masterclass')
    search_fields = ('masterclass__title',)
    readonly_fields = ('created_at', 'end_datetime')
