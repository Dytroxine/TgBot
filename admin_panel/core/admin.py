from django.contrib import admin, messages
from django.utils.html import format_html
from .models import RequiredSubscription, Category, Subcategory, Product, Cart, TelegramUser, Mailing


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ("id",)  # Отображать ID в списке
    search_fields = ("id",)  # Поле поиска по ID


@admin.register(RequiredSubscription)
class RequiredSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("channel_id", "channel_name")

    def add_view(self, request, form_url='', extra_context=None):
        # Проверяем, что пользователь на странице "Add"
        if "/add/" in request.path:
            messages.warning(
                request,
                format_html(
                    '<span style="color: yellow; font-weight: bold;">⚠️ '
                    'Бот должен быть администратором канала, чтобы проверять подписку пользователей.</span>'
                )
            )
        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        # Аналогичное предупреждение для страницы редактирования
        messages.warning(
            request,
            format_html(
                '<span style="color: yellow; font-weight: bold;"> '
                'Бот должен быть администратором канала, чтобы проверять подписку пользователей.</span>'
            )
        )
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category")

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "quantity", "subcategory")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "quantity", "updated_at")  # Отображаемые колонки
    list_filter = ("user",)  # Фильтры для удобства
    search_fields = ("user__username", "product__name")  # Поля для поиска


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ("title", "scheduled_at", "is_sent", "created_at", "last_sent_at", "preview_image")
    list_filter = ("is_sent", "scheduled_at", "created_at")
    search_fields = ("title", "message")

    readonly_fields = ("created_at", "last_sent_at", "is_sent", "preview_image")

    fieldsets = (
        (None, {
            "fields": ("title", "message", "image", "preview_image", "scheduled_at")
        }),
        ("Статус", {
            "fields": ("is_sent", "created_at", "last_sent_at")
        }),
    )

    def preview_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 200px; max-width: 300px;" />', obj.image)
        return "Нет изображения"

    preview_image.short_description = "Превью изображения"
