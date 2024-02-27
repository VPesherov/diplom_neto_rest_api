from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from backend.models import User, Shop, Product, Order, OrderItem


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    Панель управления пользователями
    """
    model = User

    # fieldsets = (
    #     (None, {'fields': ('email', 'password', 'type')}),
    #     ('Personal info', {'fields': ('first_name', 'last_name', 'company', 'position')}),
    #     ('Permissions', {
    #         'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
    #     }),
    #     ('Important dates', {'fields': ('last_login', 'date_joined')}),
    # )
    list_display = ('email', 'first_name', 'last_name', 'is_staff')


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'state']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'shop', 'price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'dt', 'state')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product_info', 'quantity')

