from django.contrib import admin
from .models import Link, ClickEvent


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ('short_code', 'original_url', 'user', 'created_at', 'expiration_date')
    search_fields = ('short_code', 'original_url')


@admin.register(ClickEvent)
class ClickEventAdmin(admin.ModelAdmin):
    list_display = ('link', 'clicked_at', 'ip_address')
    search_fields = ('link__short_code',)
