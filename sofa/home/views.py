from django.shortcuts import render,render,redirect
from . models import Products,Category,Profile,Address
from django.core.paginator import Paginator,EmptyPage,InvalidPage
from django.db.models import Count
from django.contrib.auth.models import User
from django.contrib import messages
from cart.models import *
from adminapp.models import *
from django.contrib.auth import authenticate,login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
# Create your views here.
def index(request):

    products = Products.objects.filter(soft_delete=False)
    latest_products = Products.objects.all().order_by('-created_on')[:4]
    banners=Banner.objects.all()


        
    if not request.user.is_active:
        request.session.flush()
    context={
        'products':products,
        'latest_products':latest_products,
        'banners':banners,
        
        }
    return render(request,'home/index.html',context)

def product_list(request):
    product_list = Products.objects.filter(soft_delete=False).order_by('-created_on')
    categories = Category.objects.all()
    materials = Products.objects.values_list('material', flat=True).distinct()
    colors = Products.objects.values_list('colors', flat=True).distinct()
    styles = Products.objects.values_list('style', flat=True).distinct()
    color_options = Products.objects.values_list('colors', flat=True).distinct()

    selected_categories = request.GET.getlist('category')
    selected_materials = request.GET.getlist('material')
    selected_colors = request.GET.getlist('color')
    selected_styles = request.GET.getlist('style')

    if selected_categories:
        product_list = product_list.filter(category__id__in=selected_categories)

    if selected_materials:
        product_list = product_list.filter(material__in=selected_materials)

    if selected_colors:
        product_list = product_list.filter(colors__in=selected_colors)

    if selected_styles:
        product_list = product_list.filter(style__in=selected_styles)

    paginator = Paginator(product_list, 9)
    total_items = Products.objects.aggregate(Count('product_name'))['product_name__count']

    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1

    try:
        products = paginator.page(page)
    except (EmptyPage, InvalidPage):
        products = paginator.page(paginator.num_pages)

    context = {
        'products': products,
        'categories': categories,
        'materials': materials,
        'colors': colors,
        'styles': styles,
        'total_items': total_items,
        'color_options': color_options,
        'selected_categories': selected_categories,
        'selected_materials': selected_materials,
        'selected_colors': selected_colors,
        'selected_styles': selected_styles,
    }

    return render(request, 'home/product_list.html', context)

# def product_list(request):

#     product_list=Products.objects.filter(soft_delete=False)
#     categories=Category.objects.all()

#     selected_categories = request.GET.getlist('category')  

#     if selected_categories:
#         product_list = product_list.filter(category__id__in=selected_categories)
        
#     paginator = Paginator(product_list, 9)
#     total_items = Products.objects.aggregate(Count('product_name'))['product_name__count']

#     try:
#         page = int(request.GET.get('page', 1))
#     except ValueError:
#         page = 1

#     try:
#         products = paginator.page(page)
#     except (EmptyPage, InvalidPage):
#         products = paginator.page(paginator.num_pages)
    
#     return render(request,'home/product_list.html',{'products':products,'categories':categories,'total_items': total_items,'selected_categories': selected_categories})

def product_detail(request,p_id):

    products = Products.objects.filter(soft_delete=False)[4:8]
    product_info=Products.objects.get(id=p_id)
    colors = product_info.colors.split(',') if product_info.colors else []
    materials = product_info.material.split(',') if product_info.material else []

    return render(request,'home/product_detail.html',{'product_info':product_info,'colors': colors,'materials': materials,'products':products})

def user_profile(request):
        
    return render(request,'home/user_profile.html')

@login_required
def profile(request,user_id):
    user=User.objects.get(id=user_id)
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        profile = Profile(user=user)  
        profile.save()

    context = {
        'user': user,
        'profile': profile
    }
    return render(request,'home/profile.html',context)
@login_required
def edit_user(request, user_id):
    user = User.objects.get(id=user_id)
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        profile = Profile(user=user)
        profile.save()

    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        profile_pic = request.FILES.get('profile_pic')

        if profile_pic:
            if profile.profile_image:
                # Delete the old profile image if it exists
                profile.profile_image.delete()

            profile.profile_image = profile_pic
            profile.save()

        if username:
            if User.objects.filter(username=username).exclude(id=user_id).exists():
                messages.error(request, 'Username already exists. Please choose a different username.')
            else:
                user.username = username

        user.first_name = first_name
        user.last_name = last_name
        user.save()

        return redirect('profile', user_id=user_id)

    context = {
        'user': user,
        'profile': profile
    }

    return render(request, 'home/edit_user.html', context)



@login_required
def user_address(request,user_id):
    user = User.objects.get(id=user_id)
    address_list=Address.objects.filter(user=request.user)
    sorted_addresses = sorted(address_list, key=lambda x: not x.is_default)
    if request.method=='POST':
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        paddress = request.POST.get('paddress', '')
        phone = request.POST.get('phone', '')
        locality = request.POST.get('locality', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        landmark = request.POST.get('landmark', '')
        pincode = request.POST.get('pin', '')


        if not all([first_name, last_name, email,paddress, phone, locality, city, state, landmark, pincode]):
            messages.error(request, 'All fields are required.')
            return redirect('user_address', user_id=user_id)

        if not is_valid_phone(phone):
            messages.error(request, 'Invalid phone number. Please enter a 10-digit numeric phone number.')
            return redirect('user_address', user_id=user_id)



        address=Address(
            user=request.user,
            first_name=first_name,
            landmark=landmark,
            last_name=last_name,
            phone=phone,
            email=email,
            locality=locality,
            paddress=paddress,
            city=city,
            state=state,
            pincode=pincode,
        )

        address.save()
        Address.objects.filter(user=request.user).exclude(id=address.id).update(is_default=False)
        address.is_default = True
        address.save()

        return redirect('user_address', user_id=user_id)

    context={
        'user':user,
        'address': sorted_addresses,
    }
    return render(request,'home/user_address.html',context)

def is_valid_phone(phone):
    return phone.isdigit() and len(phone) == 10

def user_order(request):
    ordered_products = OrderProduct.objects.filter(order__user=request.user)
    context = {
        'ordered_products': ordered_products,
    }
    return render(request, 'home/user_order.html', context)

def wishlist(request,product_id):
    current_user = request.user
    item = Products.objects.get(id=product_id)
    if not Wishlist.objects.filter(user=current_user, product=item).exists():
        wishlist_item = Wishlist(user=current_user, product=item)
        wishlist_item.save()
    return redirect(request.META.get('HTTP_REFERER', 'default_url'))

def user_wishlist(request,user_id):
    user=User.objects.get(id=user_id)
    wishlist_items=Wishlist.objects.filter(user=user)
    return render(request,'home/user_wishlist.html',{'wishlist_items':wishlist_items})

def remove_user_wishlist(request, product_id):
    try:
        wishlist_item = Wishlist.objects.get(id=product_id)
        user_id = wishlist_item.user.id if wishlist_item.user else None
        wishlist_item.delete()
    except Wishlist.DoesNotExist:
        user_id = None

    if user_id is not None:
        return redirect('user_wishlist', user_id=user_id)
    else:
        
        return redirect('/')

def user_order_view(request, order_id):
    global context
    order_products = OrderProduct.objects.filter(order__user=request.user, order__id=order_id)
    orders = Order.objects.filter(is_ordered=True, id=order_id)

    payments = Payment.objects.filter(orderproduct__order__id=order_id)[:1]

    for order_product in order_products:
        order_product.total = order_product.quantity * order_product.product_price
    context = {
        'order_products': order_products,
        'orders': orders,
        'payments': payments,
    }

    return render (request,'home/user_order_view.html',context)

def cancel_order(request, order_id):
 
    try:
        order = Order.objects.select_related('user').get(id=order_id, user=request.user)
        payment_methods = []
        try:
            payments = Payment.objects.filter(orderproduct__order=order)
            for payment in payments:
                payment_methods.append(payment.payment_method)
        except Payment.DoesNotExist:
            pass
        except MultipleObjectsReturned:
            pass
        if order.status in ["New", "Accepted"]:
            if "Razor pay" in payment_methods or "Wallet" in payment_methods:
                user_wallet = Wallet.objects.get_or_create(user=request.user)[0]
                user_wallet.amount += order.order_total
                user_wallet.save()                                                
            order.status = "Cancelled"
            order.save()
            for order_product in order.orderproduct_set.all():
                    product = order_product.product
                    product.quantity += order_product.quantity  # Increase the quantity
                    product.save()

    except Order.DoesNotExist:
        pass

    return redirect('user_order')

@login_required(login_url='login')
def return_order(request, order_id):
    try:
        order = Order.objects.select_related('user').get(id=order_id, user=request.user)
        order.status = "Returned"
        order.save()

        for order_product in order.orderproduct_set.all():
                product = order_product.product
                product.quantity += order_product.quantity  # Increase the quantity
                product.save()
    except Order.DoesNotExist:
        pass
    return redirect('user_order')

def user_wallet(request):

    current_user = request.user
    try:
        wallet = Wallet.objects.get(user=current_user)
    except Wallet.DoesNotExist:
        wallet = Wallet.objects.create(user=current_user, amount=0)
    wallet_amount = wallet.amount

    context = {'wallet_amount': wallet_amount}

    return render(request, 'home/user_wallet.html',context)

from django.utils import timezone

def user_coupon(request):

    all_coupons = Coupons.objects.filter(un_list=False)

    # Get used coupons by the logged-in user
    used_coupons = UserCoupons.objects.filter(user=request.user, is_used=True)
    used_coupon_ids = used_coupons.values_list('coupon_id', flat=True)

    # Get used coupon objects
    used_coupon_objects = all_coupons.filter(id__in=used_coupon_ids)

    # Filter out expired coupons from available coupons
    current_time = timezone.now()
    available_coupons = all_coupons.exclude(id__in=used_coupon_ids).filter(valid_to__gt=current_time)

    # Get expired coupons
    expired_coupons = all_coupons.exclude(id__in=used_coupon_ids).filter(valid_to__lt=current_time)
    print(expired_coupons)

    # Merge expired coupons with used coupons for displaying
    used_coupon_objects = used_coupon_objects.union(expired_coupons)
    print(used_coupon_objects)

    context = {
        'used_coupons': used_coupon_objects,
        'available_coupons': available_coupons,
    }
    
    return render(request,'home/user_coupon.html',context)