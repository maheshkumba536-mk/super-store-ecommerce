from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from datetime import timedelta


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=10, blank=True, help_text="Emoji icon (e.g., 📱, 👗, 🎧)")
    order = models.IntegerField(default=0, help_text="Display order (lower = first)")

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.icon} {self.name}" if self.icon else self.name


class ActiveProductManager(models.Manager):
    """Only returns non-expired products."""
    def get_queryset(self):
        return super().get_queryset().filter(expires_at__gt=timezone.now())


class Product(models.Model):
    STORE_CHOICES = [
        ('amazon', 'Amazon'),
        ('flipkart', 'Flipkart'),
        ('meesho', 'Meesho'),
        ('myntra', 'Myntra'),
        ('ajio', 'Ajio'),
        ('snapdeal', 'Snapdeal'),
        ('other', 'Other'),
    ]

    # Core fields
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Current/sale price")
    original_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Original price before discount (leave blank if no discount)"
    )
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    product_link = models.URLField(
        max_length=500, blank=True, null=True,
        help_text="Product buying link (Amazon, Flipkart, etc.)"
    )

    # Store and categorization
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products'
    )
    store_name = models.CharField(
        max_length=20, choices=STORE_CHOICES, default='amazon',
        help_text="Which store is this product from?"
    )
    tags = models.CharField(
        max_length=300, blank=True,
        help_text="Comma-separated tags (e.g., trending, bestseller, new)"
    )
    rating = models.DecimalField(
        max_digits=2, decimal_places=1, default=0,
        help_text="Product rating (0-5)"
    )
    is_featured = models.BooleanField(default=False, help_text="Show in featured/hero section")

    # Analytics
    click_count = models.PositiveIntegerField(default=0, help_text="Product link clicks")

    # Auto-expiry (products auto-hide after 30 days)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Product auto-hides after this date. Default: 30 days from creation."
    )

    # Managers
    objects = models.Manager()  # Default manager (all products)
    active = ActiveProductManager()  # Only non-expired products

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Auto-set expiry to 30 days from now if not set
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)

    @property
    def discount_percent(self):
        """Calculate discount percentage from original_price and price."""
        if self.original_price and self.original_price > self.price:
            return int(((self.original_price - self.price) / self.original_price) * 100)
        return 0

    @property
    def days_remaining(self):
        """Days left before product expires."""
        if self.expires_at:
            delta = self.expires_at - timezone.now()
            return max(0, delta.days)
        return 30

    @property
    def is_active(self):
        """Check if product is still active (not expired)."""
        if self.expires_at:
            return timezone.now() < self.expires_at
        return True

    @property
    def is_expiring_soon(self):
        """True if expiring within 7 days."""
        return 0 < self.days_remaining <= 7

    @property
    def store_display(self):
        """Return display name for the store."""
        return dict(self.STORE_CHOICES).get(self.store_name, self.store_name)

    @property
    def store_color(self):
        """Return brand color for the store."""
        colors = {
            'amazon': '#FF9900',
            'flipkart': '#2874F0',
            'meesho': '#F43397',
            'myntra': '#FF3F6C',
            'ajio': '#3B3B3B',
            'snapdeal': '#E40046',
            'other': '#6366F1',
        }
        return colors.get(self.store_name, '#6366F1')

    def __str__(self):
        return self.name


class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wishlist for {self.user.username}"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('wishlist', 'product')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.product.name} in {self.wishlist.user.username}'s wishlist"
