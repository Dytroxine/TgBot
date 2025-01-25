from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField

class TelegramUser(models.Model):
    id = models.BigIntegerField(primary_key=True)  # ID пользователя Telegram

    class Meta:
        db_table = "telegram_users"  # Имя таблицы в базе данных
        verbose_name = "Telegram User"
        verbose_name_plural = "Telegram Users"

    def __str__(self):
        return str(self.id)


class CommandLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    command = models.CharField(max_length=255)
    executed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.command}"


class RequiredSubscription(models.Model):
    channel_id = models.CharField(max_length=255, unique=True)
    channel_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.channel_name or self.channel_id

    class Meta:
        db_table = "required_subscriptions"

from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "categories"  # Указываем имя таблицы в базе данных

    def __str__(self):
        return self.name

class Subcategory(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="subcategories")

    class Meta:
        db_table = "subcategories"  # Указываем имя таблицы в базе данных

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=0)
    photo_url = models.URLField(blank=True, null=True)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, related_name="products")

    class Meta:
        db_table = "products"  # Указываем имя таблицы в базе данных

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)  # Пользователь
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Продукт
    quantity = models.PositiveIntegerField(default=1)  # Количество
    updated_at = models.DateTimeField(auto_now=True)  # Время последнего обновления

    class Meta:
        unique_together = ("user", "product")  # Один пользователь — один продукт в корзине
        db_table = "cart"

    def __str__(self):
        return f"{self.user} | {self.product.name} | {self.quantity} шт."


class Mailing(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название рассылки")
    message = models.TextField(verbose_name="Текст сообщения")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    scheduled_at = models.DateTimeField(verbose_name="Время запланированной рассылки", null=True, blank=True)
    is_sent = models.BooleanField(default=False, verbose_name="Отправлено")
    image = models.URLField(blank=True, null=True, verbose_name="Изображение")  # Новое поле
    last_sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата последней отправки")

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ["-created_at"]
        db_table = "mailings"

    def __str__(self):
        return self.title
