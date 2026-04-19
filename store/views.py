from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Cart, CartItem, Order, OrderItem
from django.db import transaction

# Create your views here.

def home(request):
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'store/home.html', {'products': products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'store/product_detail.html', {'product': product})

def register_user(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Cart.objects.create(user=user) # Create a cart for new user
            login(request, user)
            messages.success(request, "Registration successful.")
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
                # Ensure user has a cart
                Cart.objects.get_or_create(user=user)
                messages.info(request, f"You are now logged in as {username}.")
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

@login_required(login_url='login')
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.all()
    total = sum(item.total_price for item in items)
    return render(request, 'store/cart.html', {'items': items, 'total': total, 'cart': cart})

@login_required(login_url='login')
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f"{product.name} added to your cart.")
    return redirect('cart_view')

@login_required(login_url='login')
def update_cart(request, pk):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()
        except ValueError:
            pass
    return redirect('cart_view')

@login_required(login_url='login')
def remove_from_cart(request, pk):
    cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    cart_item.delete()
    messages.info(request, "Item removed from cart.")
    return redirect('cart_view')

@login_required(login_url='login')
@transaction.atomic
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    items = cart.items.all()
    
    if not items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('cart_view')
        
    if request.method == 'POST':
        total = sum(item.total_price for item in items)
        order = Order.objects.create(user=request.user, total_price=total, is_completed=True)
        
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price_at_purchase=item.product.price
            )
            
        items.delete() # Clear cart
        return redirect('order_success')
        
    total = sum(item.total_price for item in items)
    return render(request, 'store/checkout.html', {'items': items, 'total': total})

@login_required(login_url='login')
def order_success(request):
    return render(request, 'store/order_success.html')
