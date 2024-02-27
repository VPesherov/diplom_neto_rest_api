from rest_framework import serializers

from backend.models import User, Product, Order, OrderItem


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'username')
        read_only_fields = ('id',)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'name', 'description', 'price',)
        read_only_fields = ('id',)


class OrderSerializer(serializers.ModelSerializer):
    total_sum = serializers.IntegerField()

    class Meta:
        model = Order
        fields = ('id', 'ordered_items', 'state', 'dt', 'total_sum')
        read_only_fields = ('id',)


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ('id', 'order', 'product_info', 'quantity',)
        read_only_fields = ('id',)
