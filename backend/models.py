from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_rest_passwordreset.tokens import get_token_generator

STATE_CHOICES = (
    ('basket', 'Статус корзины'),
    ('new', 'Новый'),
    ('confirmed', 'Подтвержден'),
    ('assembled', 'Собран'),
    ('sent', 'Отправлен'),
    ('delivered', 'Доставлен'),
    ('canceled', 'Отменен'),
)

USER_TYPE_CHOICES = (
    ('shop', 'Магазин'),
    ('buyer', 'Покупатель'),

)


# Create your models here.


class UserManager(BaseUserManager):
    """
    Миксин для управления пользователями
    """
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not email:
            raise ValueError('Отсутсвует email')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        # user.USERNAME_FIELD
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser должен иметь права is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser должен иметь права is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Стандартная модель пользователей
    """
    REQUIRED_FIELDS = []
    objects = UserManager()
    USERNAME_FIELD = 'email'
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(
        _('username'),
        max_length=100,
        help_text=_('Не более 100 символов.'),
        error_messages={
            'unique': "Пользователь с таким username уже существует",
        },
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Определяет, следует ли считать этого пользователя активным. Снимите этот флажок вместо удаления учетных '
            'записей.'
        ),
    )
    type = models.CharField(verbose_name='Тип пользователя', choices=USER_TYPE_CHOICES, max_length=5, default='buyer')

    delivery_address = models.TextField(default="", blank=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name} {self.email}'

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = "Список пользователей"
        ordering = ('email',)


class Shop(models.Model):
    # objects = models.manager.Manager()
    name = models.CharField(max_length=50, verbose_name='Название')
    # url = models.URLField(verbose_name='Ссылка', null=True, blank=True)
    user = models.ForeignKey(User, verbose_name='Владелец',
                             related_name='users', blank=True,
                             on_delete=models.CASCADE)
    # user = models.ManyToOneRel(User)
    state = models.BooleanField(verbose_name='статус получения заказов', default=True)

    # filename

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = "Список магазинов"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class Product(models.Model):
    # objects = models.manager.Manager()
    name = models.CharField(max_length=80, verbose_name='Название')
    shop = models.ForeignKey(Shop, verbose_name='Продавец',
                             related_name='shops', blank=True,
                             on_delete=models.CASCADE)

    price = models.PositiveIntegerField(null=True)
    # description1 = models.TextField(blank=True, default='')
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = "Список продуктов"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class Order(models.Model):
    # objects = models.manager.Manager()
    user = models.ForeignKey(User, verbose_name='Пользователь',
                             related_name='orders', blank=True,
                             on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)
    state = models.CharField(verbose_name='Статус', choices=STATE_CHOICES, max_length=15)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = "Список заказ"
        ordering = ('-dt',)

    def __str__(self):
        return f'{self.id} | {str(self.dt)} | {self.state}'

    # @property
    # def sum(self):
    #     return self.ordered_items.aggregate(total=Sum("quantity"))["total"]


class OrderItem(models.Model):
    # objects = models.manager.Manager()
    order = models.ForeignKey(Order, verbose_name='Заказ', related_name='ordered_items', blank=True,
                              on_delete=models.CASCADE)

    product_info = models.ForeignKey(Product, verbose_name='Информация о продукте', related_name='ordered_items',
                                     blank=True,
                                     on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Заказанная позиция'
        verbose_name_plural = "Список заказанных позиций"
        constraints = [
            models.UniqueConstraint(fields=['order_id', 'product_info'], name='unique_order_item'),
        ]
