from django.contrib import admin

from .models import Subscribe, User


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email')
    list_filter = ('username', 'email')


class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'following')


admin.site.register(User, UserAdmin)
admin.site.register(Subscribe, SubscribeAdmin)
