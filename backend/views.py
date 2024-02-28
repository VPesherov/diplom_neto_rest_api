from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import IntegrityError
from django.db.models import Sum, F
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from requests import get
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from yaml import load as load_yaml, Loader
from ujson import loads as load_json
from django.core.mail import send_mail
from django.conf import settings

from backend.models import Shop, Product, User, Order, OrderItem
from backend.serializers import UserSerializer, ProductSerializer, OrderSerializer, OrderItemSerializer

from annoying.functions import get_object_or_None


# Create your views here.


# загрузка товаров из yaml файла

class CatalogUpdate(APIView):
    def post(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return JsonResponse({'Status': "Error", 'Error': 'Для выполнение данной операции нужно авторизоваться'},
                                status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': "Error", 'Error': 'Только для магазинов'}, status=403)

        file = request.data.get('file')
        data = load_yaml(file, Loader=Loader)
        shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)

        if data:
            try:
                for item in data['goods']:
                    Product.objects.get_or_create(name=item['name'], shop=shop, price=item['price'],
                                                  description=item['description'])
            except Exception as exc:
                return JsonResponse({'Status': "Error", 'Error': 'Непредвиденная ошибка'})
            return JsonResponse({'Status': "Success"})

        return JsonResponse({'Status': "Error", 'Errors': 'Не указаны все необходимые аргументы'})


class RegisterAccount(APIView):

    # Регистрация методом POST

    def post(self, request, *args, **kwargs):
        # проверяем обязательные аргументы
        if {'username', 'first_name', 'last_name', 'email', 'password', 'username'}.issubset(request.data):

            # проверяем пароль на сложность
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                # noinspection PyTypeChecker
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': "Error", 'Errors': {'password': error_array}})
            else:
                # проверяем данные для уникальности имени пользователя
                # request.data[""]
                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    # сохраняем пользователя
                    user = user_serializer.save()
                    user.set_password(request.data['password'])
                    user.save()
                    return JsonResponse({'Status': "Success"})
                else:
                    return JsonResponse({'Status': "Error", 'Errors': user_serializer.errors})

        return JsonResponse({'Status': "ErRor", 'Errors': 'Не указаны все необходимые аргументы'})


class SignIn(APIView):
    def post(self, request, *args, **kwargs):

        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['email'], password=request.data['password'])

            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)

                    return JsonResponse({'Status': "Success", 'Token': token.key})

            return JsonResponse({'Status': "Error", 'Errors': 'Пользователь не найден'})

        return JsonResponse({'Status': "Error", 'Errors': 'Не указаны все необходимые аргументы'})


class PasswordRecovery(APIView):
    new_password = 'safa1235fa21'

    # сделал сброс пароля, и установление его по умолчанию при верно введёных email, first_name, last_name
    # по хорошему после ввода этих данных - пользователю должны данные отправляться на почту

    def patch(self, request, *args, **kwargs):
        if {'email', 'first_name', 'last_name'}.issubset(request.data):
            user = get_object_or_None(User, email=request.data['email'], first_name=request.data["first_name"],
                                      last_name=request.data['last_name'])
            if user:
                user_serializer = UserSerializer(user, data=request.data, partial=True)
                if user_serializer.is_valid():
                    user = user_serializer.save()
                    user.set_password(PasswordRecovery.new_password)
                    user.save()
                    return JsonResponse({'Status': "Success",
                                         "Message": f"Пароль успешно изменён. Новый пароль:\n{PasswordRecovery.new_password}"})
                else:
                    return JsonResponse({'Status': "Error", 'Errors': user_serializer.errors})
            else:
                return JsonResponse({'Status': "Error", "Error": "Введены неверные данные"})
        else:
            return JsonResponse(
                {'Status': "Error", 'Errors': "Для сброса пароля необходимы email, first_name, last_name"})


# каталог продуктов

class ProductView(APIView):
    def get(self, request, product_id=None):
        if product_id:
            products = Product.objects.filter(id=product_id)
        else:
            products = Product.objects.all()
        product_serializer = ProductSerializer(products, many=True)
        return Response(product_serializer.data)


# действия с корзиноы

class BasketView(APIView):
    # получить корзину
    def get(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return JsonResponse({'Status': "Error", 'Error': 'Для выполнение данной операции нужно авторизоваться'},
                                status=403)
        basket = Order.objects.filter(
            user_id=request.user.id, state='basket').prefetch_related('ordered_items__product_info').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data)

    # пополнить корзину
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': "Error", 'Error': 'Для выполнение данной операции нужно авторизоваться'},
                                status=403)
        try:
            items_sting = request.data.get('items')
            basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
            objects_created = 0
            try:
                for order_item in items_sting:
                    product = get_object_or_None(Product, id=order_item["id"])
                    if not product:
                        return JsonResponse({'Status': "Error", "Error": f"Товар {product} отсутствует"})

                    if not product.shop.state:
                        return JsonResponse({'Status': "Error",
                                             "Error": f"Товар {product} не может быть добавлен в корзину, так как "
                                                      f"продавец {product.shop.name} не принимает заказы"})

                    order, _ = OrderItem.objects.get_or_create(order=basket, product_info=product,
                                                               quantity=order_item["quantity"])
                    order.save()
                    objects_created += 1
            except IntegrityError as exc:
                return JsonResponse({'Status': "Error", 'Error': 'Данный товар находится уже в вашей корзине'})

            return JsonResponse({'Status': "Success", 'Товаров добавлено в корзину': objects_created})
        except Exception as exc:
            return JsonResponse({'Status': "Error", 'Errors': 'Непредвиденная ошибка'})

    # удалить товары из корзины
    def delete(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return JsonResponse({'Status': "Error", 'Error': 'Для выполнение данной операции нужно авторизоваться'},
                                status=403)

        try:
            items_sting = request.data.get('items')
            basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
            for order_item in items_sting:
                product = get_object_or_None(Product, id=order_item["product_id"])
                if not product:
                    return JsonResponse({'Status': "Error", "Error1": f"Товар {product} отсутствует"})
                order, _ = OrderItem.objects.get_or_create(order=basket, product_info=product)
                deleted_count = OrderItem.objects.filter(order=basket, product_info=product).delete()[0]

            return JsonResponse({'Status': "Success", 'Товаров удалено из корзины': deleted_count})

        except Exception as exc:
            return JsonResponse({'Status': "Error2", 'Errors': 'Непредвиденная ошибка'})


class DeliveryAddressView(APIView):
    def patch(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return JsonResponse({'Status': "Error", 'Error': 'Для выполнение данной операции нужно авторизоваться'},
                                status=403)

        if {'delivery_address'}.issubset(request.data):
            user = User.objects.get(id=request.user.id)
            new_address = request.data.get('delivery_address')
            user.delivery_address = new_address
            user.save()
            # serializer = UserSerializer(user)
            return JsonResponse({'Status': "Success"})
        else:
            return JsonResponse({'Status': "Error", "Error": "Не указан адрес"})

    def delete(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': "Error", 'Error': 'Для выполнение данной операции нужно авторизоваться'},
                                status=403)
        user = User.objects.get(id=request.user.id)
        user.delivery_address = ''
        user.save()
        return JsonResponse({'Status': "Success"})


# подтверждение заказа(без Email((( )
class ConfirmedOrderByUserView(APIView):
    def patch(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': "Error", 'Error': 'Для выполнение данной операции нужно авторизоваться'},
                                status=403)
        basket = get_object_or_None(Order, user_id=request.user.id, state='basket')
        if basket:

            order_item = OrderItem.objects.filter(order=basket).count()
            if order_item == 0:
                return JsonResponse({"Status": "Error", "Error": "Вы не можете подтвердить пустой заказ"})

            user = User.objects.get(id=request.user.id)
            if user.delivery_address == '':
                return JsonResponse({"Status": "Error", "Error": "Для подтверждения заказа необходимо указать адрес"})

            basket.state = 'confirmed'
            basket.save()
            return JsonResponse({"Status": "Success"})

        return JsonResponse({"Status": "Error", "Error": "Заказ не найден"})


# получение заказа и выбранного заказа по id
class UserOrderView(APIView):
    def get(self, request, order_id=None):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': "Error", 'Error': 'Для выполнение данной операции нужно авторизоваться'},
                                status=403)

        if order_id:
            orders = Order.objects.filter(
                user_id=request.user.id, id=order_id).prefetch_related('ordered_items__product_info').annotate(
                total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
        else:
            orders = Order.objects.filter(
                user_id=request.user.id).prefetch_related('ordered_items__product_info').annotate(
                total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
        order_serializer = OrderSerializer(orders, many=True)
        # return JsonResponse({"State": 1})
        return Response(order_serializer.data)

    def patch(self, request, order_id):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': "Error", 'Error': 'Для выполнение данной операции нужно авторизоваться'},
                                status=403)

        state = request.data.get('state')

        if request.user.type == 'user' and state != 'canceled':
            return JsonResponse({'Status': "Error", '1Error': 'Вы не можете накладывать данный статус на заказ'},
                                status=403)

        elif request.user.type == 'shop' and state not in ('assembled', 'sent', 'delivered', 'canceled'):
            return JsonResponse({'Status': "Error", '2Error': 'Вы не можете накладывать данный статус на заказ'},
                                status=403)
        order = get_object_or_None(Order, id=order_id)

        if not order:
            return JsonResponse({"Status": "Error", "Error": "Данный заказ не найден"})

        order.state = state
        order.save()

        return JsonResponse({"Status": "Success"})

# не работает(

# def send_custom_email(subject, message, recipient_list):
#     # Send the email using Django's send_mail function
#     send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list)
#
#
# def my_email_view(request):
#     # ... Your view logic ...
#
#     subject = 'Hello from Django'
#     message = 'This is a test email sent from Django.'
#     recipient_list = ['frobbyword@yandex.ru']  # Replace with the recipient's email addresses
#
#     send_custom_email(subject, message, recipient_list)
#
#     # ... Rest of your view logic ...
#     return HttpResponse("Normal Email Send Successfully!")
