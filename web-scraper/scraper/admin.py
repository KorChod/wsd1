from django.contrib import admin
from .models import Image, WebPage, AsyncResults


@admin.register(WebPage)
class WebPageAdmin(admin.ModelAdmin):
    pass


@admin.register(Image)
class ImagePageAdmin(admin.ModelAdmin):
    pass


@admin.register(AsyncResults)
class AsyncResultAdmin(admin.ModelAdmin):
    pass
