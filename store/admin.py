from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta
from .models import Category, Product, Wishlist, WishlistItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('icon_display', 'name', 'slug', 'product_count', 'order')
    list_editable = ('order',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

    def icon_display(self, obj):
        return obj.icon or '📁'
    icon_display.short_description = 'Icon'

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


class ExpiredFilter(admin.SimpleListFilter):
    title = 'Expiry Status'
    parameter_name = 'expiry'

    def lookups(self, request, model_admin):
        return (
            ('active', '✅ Active'),
            ('expiring_soon', '⚠️ Expiring Soon (< 7 days)'),
            ('expired', '❌ Expired'),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'active':
            return queryset.filter(expires_at__gt=now + timedelta(days=7))
        if self.value() == 'expiring_soon':
            return queryset.filter(expires_at__gt=now, expires_at__lte=now + timedelta(days=7))
        if self.value() == 'expired':
            return queryset.filter(expires_at__lte=now)
        return queryset


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'image_preview', 'name', 'price', 'original_price',
        'discount_display', 'store_badge', 'category',
        'click_count', 'days_left', 'is_featured', 'created_at'
    )
    list_editable = ('price', 'original_price', 'is_featured')
    list_filter = ('store_name', 'category', 'is_featured', ExpiredFilter)
    search_fields = ('name', 'description', 'tags')
    readonly_fields = ('click_count', 'image_preview_large', 'created_at')
    list_per_page = 25

    fieldsets = (
        ('📦 Product Info', {
            'fields': ('name', 'description', 'image', 'image_preview_large', 'category', 'tags')
        }),
        ('💰 Pricing', {
            'fields': ('price', 'original_price', 'rating')
        }),
        ('🔗 Affiliate Link', {
            'fields': ('product_link', 'store_name', 'click_count')
        }),
        ('⚙️ Settings', {
            'fields': ('is_featured', 'expires_at', 'created_at')
        }),
    )

    actions = ['make_featured', 'remove_featured', 'extend_expiry_30', 'delete_expired']

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:50px; height:50px; object-fit:cover; border-radius:8px; border:1px solid #e5e7eb;" />',
                obj.image.url
            )
        return format_html('<span style="color:#9ca3af;">No img</span>')
    image_preview.short_description = 'Image'

    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:300px; border-radius:12px; border:1px solid #e5e7eb;" />',
                obj.image.url
            )
        return 'No image uploaded'
    image_preview_large.short_description = 'Preview'

    def discount_display(self, obj):
        pct = obj.discount_percent
        if pct > 0:
            return format_html(
                '<span style="background:#ef4444; color:white; padding:2px 8px; border-radius:12px; font-size:0.8rem; font-weight:600;">{}% OFF</span>',
                pct
            )
        return '-'
    discount_display.short_description = 'Discount'

    def store_badge(self, obj):
        return format_html(
            '<span style="background:{}; color:white; padding:2px 10px; border-radius:12px; font-size:0.8rem; font-weight:500;">{}</span>',
            obj.store_color, obj.store_display
        )
    store_badge.short_description = 'Store'

    def days_left(self, obj):
        days = obj.days_remaining
        if days == 0:
            return format_html(
                '<span style="background:#ef4444; color:white; padding:2px 10px; border-radius:12px; font-size:0.8rem;">❌ Expired</span>'
            )
        elif days <= 7:
            return format_html(
                '<span style="background:#f59e0b; color:white; padding:2px 10px; border-radius:12px; font-size:0.8rem;">⚠️ {} days</span>',
                days
            )
        elif days <= 15:
            return format_html(
                '<span style="background:#eab308; color:white; padding:2px 10px; border-radius:12px; font-size:0.8rem;">🟡 {} days</span>',
                days
            )
        else:
            return format_html(
                '<span style="background:#10b981; color:white; padding:2px 10px; border-radius:12px; font-size:0.8rem;">✅ {} days</span>',
                days
            )
    days_left.short_description = 'Expires In'

    @admin.action(description='⭐ Mark as Featured')
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)

    @admin.action(description='Remove from Featured')
    def remove_featured(self, request, queryset):
        queryset.update(is_featured=False)

    @admin.action(description='🔄 Extend Expiry by 30 Days')
    def extend_expiry_30(self, request, queryset):
        for product in queryset:
            product.expires_at = timezone.now() + timedelta(days=30)
            product.save()
        self.message_user(request, f"Extended expiry for {queryset.count()} products.")

    @admin.action(description='🗑️ Delete Expired Products')
    def delete_expired(self, request, queryset):
        expired = queryset.filter(expires_at__lte=timezone.now())
        count = expired.count()
        expired.delete()
        self.message_user(request, f"Deleted {count} expired products.")


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'item_count', 'created_at')

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('wishlist', 'product', 'added_at')
