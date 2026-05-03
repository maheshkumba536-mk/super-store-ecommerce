from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from .models import Product, Category, Wishlist, WishlistItem


def home(request):
    """Homepage with featured products, categories, and product grid."""
    products = Product.active.all().order_by('-is_featured', '-created_at')
    categories = Category.objects.all()
    featured = Product.active.filter(is_featured=True)[:6]

    # Category filter
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)

    # Store filter
    store = request.GET.get('store')
    if store:
        products = products.filter(store_name=store)

    context = {
        'products': products,
        'categories': categories,
        'featured': featured,
        'active_category': category_slug,
        'active_store': store,
        'stores': Product.STORE_CHOICES,
    }
    return render(request, 'store/home.html', context)


def product_detail(request, pk):
    """Product detail page with sharing options."""
    product = get_object_or_404(Product, pk=pk)

    # Check if expired
    if not product.is_active:
        messages.warning(request, "This deal has expired.")
        return redirect('home')

    # Related products (same category, excluding current)
    related = Product.active.filter(
        category=product.category
    ).exclude(pk=pk)[:4] if product.category else Product.active.exclude(pk=pk)[:4]

    # Check if in user's wishlist
    in_wishlist = False
    if request.user.is_authenticated:
        wishlist = Wishlist.objects.filter(user=request.user).first()
        if wishlist:
            in_wishlist = WishlistItem.objects.filter(
                wishlist=wishlist, product=product
            ).exists()

    # Build full URL for sharing
    full_url = request.build_absolute_uri()

    context = {
        'product': product,
        'related': related,
        'in_wishlist': in_wishlist,
        'full_url': full_url,
    }
    return render(request, 'store/product_detail.html', context)


def search_products(request):
    """Search products via AJAX or regular request."""
    query = request.GET.get('q', '').strip()
    products = Product.active.all()

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query)
        )

    store = request.GET.get('store')
    if store:
        products = products.filter(store_name=store)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX response
        data = [{
            'id': p.pk,
            'name': p.name,
            'price': str(p.price),
            'original_price': str(p.original_price) if p.original_price else None,
            'discount_percent': p.discount_percent,
            'image': p.image.url if p.image else None,
            'store_name': p.store_display,
            'store_color': p.store_color,
            'rating': str(p.rating),
            'days_remaining': p.days_remaining,
            'is_expiring_soon': p.is_expiring_soon,
            'product_link': p.product_link or '#',
        } for p in products[:20]]
        return JsonResponse({'products': data})

    categories = Category.objects.all()
    context = {
        'products': products,
        'query': query,
        'categories': categories,
        'active_store': store,
        'stores': Product.STORE_CHOICES,
    }
    return render(request, 'store/home.html', context)


def category_view(request, slug):
    """Products filtered by category."""
    category = get_object_or_404(Category, slug=slug)
    products = Product.active.filter(category=category)
    categories = Category.objects.all()

    store = request.GET.get('store')
    if store:
        products = products.filter(store_name=store)

    context = {
        'products': products,
        'categories': categories,
        'active_category': slug,
        'current_category': category,
        'active_store': store,
        'stores': Product.STORE_CHOICES,
    }
    return render(request, 'store/home.html', context)


def track_click(request, pk):
    """Track affiliate link click and redirect to external store."""
    product = get_object_or_404(Product, pk=pk)
    product.click_count += 1
    product.save(update_fields=['click_count'])

    if product.product_link:
        return redirect(product.product_link)
    return redirect('product_detail', pk=pk)


@login_required(login_url='login')
def wishlist_view(request):
    """View user's wishlist."""
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    items = wishlist.items.select_related('product').all()

    # Filter out expired products from wishlist display
    active_items = [item for item in items if item.product.is_active]

    context = {
        'items': active_items,
        'wishlist': wishlist,
    }
    return render(request, 'store/wishlist.html', context)


@login_required(login_url='login')
def toggle_wishlist(request, pk):
    """Add/remove product from wishlist (AJAX)."""
    product = get_object_or_404(Product, pk=pk)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)

    item = WishlistItem.objects.filter(wishlist=wishlist, product=product).first()

    if item:
        item.delete()
        added = False
        message = f"{product.name} removed from wishlist."
    else:
        WishlistItem.objects.create(wishlist=wishlist, product=product)
        added = True
        message = f"{product.name} added to wishlist!"

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'added': added,
            'message': message,
            'count': wishlist.items.count(),
        })

    messages.success(request, message)
    return redirect(request.META.get('HTTP_REFERER', 'home'))


def pinterest_feed(request):
    """Pinterest-optimized product feed for bulk pinning."""
    products = Product.active.all().order_by('-created_at')[:50]
    context = {
        'products': products,
    }
    return render(request, 'store/pinterest_feed.html', context)


# ---- Auth Views ----

def register_user(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Wishlist.objects.create(user=user)  # Create wishlist for new user
            login(request, user)
            messages.success(request, "Welcome! Your account has been created. 🎉")
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'store/register.html', {'form': form})


def login_user(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                Wishlist.objects.get_or_create(user=user)
                messages.info(request, f"Welcome back, {username}! 👋")
                return redirect('home')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'store/login.html', {'form': form})


def logout_user(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('home')
