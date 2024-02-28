"""
URL configuration for diplom project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django_rest_passwordreset.views import reset_password_request_token

from backend.views import CatalogUpdate, RegisterAccount, SignIn, PasswordRecovery, ProductView, BasketView, \
    DeliveryAddressView, ConfirmedOrderByUserView, UserOrderView

app_name = 'backend'
urlpatterns = [
    path('admin/', admin.site.urls),
    path('catalog/update', CatalogUpdate.as_view(), name='catalog-update'),
    path('user/register', RegisterAccount.as_view(), name='user-register'),
    path('user/signin', SignIn.as_view(), name='user-sign-in'),
    path('user/password_reset', PasswordRecovery.as_view(), name='password-reset'),
    path('catalog/', ProductView.as_view(), name='catalog'),
    path('catalog/<int:product_id>/', ProductView.as_view(), name='catalog'),
    path('basket/', BasketView.as_view(), name='basket'),
    path('change_delivery_address/', DeliveryAddressView.as_view(), name='delivery-address'),
    path('confirmed_order_by_user/', ConfirmedOrderByUserView.as_view(), name='confirmed-order-user'),
    path('user/orders/', UserOrderView.as_view(), name='shop-orders'),
    path('user/orders/<int:order_id>/', UserOrderView.as_view(), name='shop-orders'),
    # path('user/orders/<int:order_id>/', UserOrderView.as_view(), name='shop-orders'),
    # path('email/', my_email_view, name='normal-email')
]

