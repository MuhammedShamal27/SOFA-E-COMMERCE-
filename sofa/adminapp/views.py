from django.shortcuts import get_object_or_404, render,redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.contrib.auth.models import User
from home.models import *
from cart.models import *
from . models import *
from django.core.paginator import Paginator,EmptyPage,InvalidPage
from datetime import datetime, timedelta, time
from django.db.models import F, Sum, Count,Q
from django.db.models.functions import TruncMonth, TruncYear
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound, JsonResponse
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO
import re
# Create your views here.

@login_required
def admin_home(request):
    if request.user.is_anonymous or not request.user.is_superuser:
        return redirect('admin_login')
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    total_ordered_orders = Order.objects.filter(is_ordered=True).count()
    total_available_products = Products.objects.filter(soft_delete=False, category__is_soft_delete=False).count()
    total_available_category = Category.objects.filter(is_soft_delete=False).count()
    total_delivered = Order.objects.filter(is_ordered=True, status='Delivered').count()
    total_pending = Order.objects.filter(is_ordered=True, status='New').count()
    total_cancelled = Order.objects.filter(is_ordered=True, status='Cancelled').count()
    total_returned = Order.objects.filter(is_ordered=True, status='Returned').count()

    total_earned_amount = \
        Order.objects.filter(is_ordered=True).exclude(status__in=['Cancelled', 'Returned']).aggregate(
            Sum('order_total'))[
            'order_total__sum'] or 0


    daily_order_counts = (
        Order.objects
        .filter(created_at__range=(start_date, end_date), is_ordered=True)
        .values('created_at__date')
        .annotate(order_count=Count('id'))
        .order_by('created_at__date')
    )

    monthly_order_counts = (
        Order.objects
        .filter(created_at__year=end_date.year, is_ordered=True)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(order_count=Count('id'))
        .order_by('month')
    )

    yearly_order_counts = (
        Order.objects
        .filter(created_at__year=end_date.year, is_ordered=True)
        .annotate(year=TruncYear('created_at'))
        .values('year')
        .annotate(order_count=Count('id'))
        .order_by('year')
    )

    dates = [entry['created_at__date'].strftime('%Y-%m-%d') for entry in daily_order_counts]
    counts = [entry['order_count'] for entry in daily_order_counts]
    monthly_dates = [entry['month'].strftime('%Y-%m') for entry in monthly_order_counts]
    monthly_counts = [entry['order_count'] for entry in monthly_order_counts]

    yearly_dates = [entry['year'].strftime('%Y') for entry in yearly_order_counts]
    yearly_counts = [entry['order_count'] for entry in yearly_order_counts]

    orders = Order.objects.filter(is_ordered=True).order_by('-created_at')[:10]
    context={
        'total_ordered_orders': total_ordered_orders,
        'total_available_products': total_available_products,
        'total_available_category': total_available_category,
        'total_earned_amount': total_earned_amount,
        'total_delivered': total_delivered,
        'total_pending': total_pending,
        'total_returned': total_returned,
        'total_cancelled': total_cancelled,
        'orders': orders,
        'dates': dates,
        'counts': counts,
        'monthly_dates': monthly_dates,
        'monthly_counts': monthly_counts,
        'yearly_dates': yearly_dates,
        'yearly_counts': yearly_counts,
    }
    return render(request,'adminapp/admin_home.html',context)


def admin_login(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin_home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user is not None and user.is_superuser and user.is_active:
            request.session['super_user'] = username
            login(request, user)
            return redirect('admin_home')
        else:
            messages.error(request, "Invalid credentials. Please Try again.")
            return redirect('admin_login')
    return render(request,'adminapp/admin_login.html')

@login_required(login_url='admin_login')
def customer(request):
    # if not 'super_user' in request.session:
    #     return redirect('admin_login')
    
    if not request.user.is_superuser:
        return redirect('admin_login')
    customers_list=User.objects.filter(is_superuser=False).order_by('username')
    paginator = Paginator(customers_list, 10)
    try:
        page = int(request.GET.get('page', 1))
    except:
        page = 1
    try:
        customers = paginator.page(page)
    except (EmptyPage, InvalidPage):
        customers = paginator.page(paginator.num_pages)

    # customers = User.objects.filter(is_superuser=False)
    # context = {'customers': customers}
    return render(request,'adminapp/customer.html',{'customers':customers})


def block_user(request,u_id):
    user = User.objects.get(id=u_id)
    if not user.is_superuser:
        user.is_active = False
        user.save()
        print(user.is_active)

        # Optionally, you can also log out the user if they are currently logged in
        if request.user.is_authenticated and request.user.id == user.id:
            logout(request)

        messages.success(request, f"User {user.username} has been blocked.")
    return redirect('customer')


def unblock_user(request,u_id):
    try:
        user = User.objects.get(id=u_id)
        user.is_active = True
        user.save()
        print(user.is_active)
        messages.success(request, f'User "{user.username}" has been unblocked.')
    except User.DoesNotExist:
        messages.error(request, 'User does not exist.')
        return redirect('customer')

    return redirect('customer')



@login_required(login_url='admin_login')
def add_product(request):
    if not request.user.is_superuser:
        return redirect('admin_login')

    categories = Category.objects.filter(is_soft_delete=False)

    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        material = request.POST.get('material')
        orginal_price = request.POST.get('orginal_price')  
        offer_price = request.POST.get('offer_price')  
        style = request.POST.get('style')
        description = request.POST.get('description')
        quantity = request.POST.get('quantity')
        seating = request.POST.get('seating')
        color = request.POST.get('colors')
        category_id = request.POST.get('category')

        images = [request.FILES.get(f'image{i}') for i in range(1, 6)]
        crops = [
            (
                float(request.POST.get(f'crop_x{i}', 0)) if request.POST.get(f'crop_x{i}') else 0,
                float(request.POST.get(f'crop_y{i}', 0)) if request.POST.get(f'crop_y{i}') else 0,
                float(request.POST.get(f'crop_width{i}', 0)) if request.POST.get(f'crop_width{i}') else 0,
                float(request.POST.get(f'crop_height{i}', 0)) if request.POST.get(f'crop_height{i}') else 0
            )
            for i in range(1, 6)
        ]

        # Validate form inputs

        if not all([product_name, material, orginal_price, offer_price, style, description,
                    quantity, seating, color, category_id]) or any(not image for image in images):
            messages.error(request, 'Please provide all the required fields')
            return redirect('add_product')

        try:
            orginal_price = int(orginal_price)
            offer_price = int(offer_price)
        except ValueError:
            messages.error(request, 'Orginal price and offer price must be valid numbers')
            return redirect('add_product')

        if offer_price > orginal_price or offer_price < 0 or orginal_price < 0:
            messages.error(request, 'Invalid price values')
            return redirect('add_product')

        if not all(images):
            messages.error(request, 'Please upload all images')
            return redirect('add_product')

        try:
            category = Category.objects.get(id=category_id, is_soft_delete=False)
        except Category.DoesNotExist:
            messages.error(request, 'Invalid category')
            return redirect('add_product')

        product = Products(
            product_name=product_name,
            material=material,
            orginal_price=orginal_price,
            offer_price=offer_price,
            style=style,
            description=description,
            quantity=quantity,
            seating=seating,
            category=category,
            colors=color,
        )
        product.save()

        for i, (image, crop) in enumerate(zip(images, crops), start=1):
            try:
                image_content = BytesIO(image.read())
                original_image = Image.open(image_content)
                cropped_image = original_image.crop(crop)
                cropped_image_content = BytesIO()
                cropped_image.save(cropped_image_content, format='JPEG')

                # Ensure the cropped image content is saved as a valid Django file
                product_image_field = getattr(product, f'product_image{i}')
                product_image_field.save(f'image{i}.jpg', ContentFile(cropped_image_content.getvalue()), save=False)
            except Exception as e:
                messages.error(request, f'Error processing image {i}: {str(e)}')
                return redirect('add_product')

        # Save the product with processed images
        product.save()

        return redirect('admin_product_list')

    return render(request, 'adminapp/add_product.html', {'categories': categories})


@login_required(login_url='admin_login')
def admin_product_list(request):

    if not request.user.is_superuser:
        return redirect('admin_login')
    
    # categories = Category.objects.all()
    product_list=Products.objects.all().order_by('-created_on')
    paginator=Paginator(product_list,5)

    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1

    # selected_category = request.GET.get('selected_category')

    # if selected_category:
    #     product_list = Products.objects.filter(category_id=selected_category).order_by('created_on')


    try:
        products=paginator.page(page)
    except(EmptyPage,InvalidPage):
        products=Paginator.page(paginator.num_pages)

        
    return render(request,'adminapp/admin_product_list.html',{'products':products})


def edit_products(request, p_id):
    if not request.user.is_superuser:
        return redirect('admin_login')

    product = Products.objects.get(id=p_id)
    category_all = Category.objects.all()

    if request.method == "POST":
        product_name = request.POST.get('product_name')
        material = request.POST.get('material')
        orginal_price = request.POST.get('orginal_price')
        offer_price = request.POST.get('offer_price')
        style = request.POST.get('style')
        description = request.POST.get('description')
        image1 = request.FILES.get('image1')
        image2 = request.FILES.get('image2')
        image3 = request.FILES.get('image3')
        image4 = request.FILES.get('image4')
        image5 = request.FILES.get('image5')
        quantity = request.POST.get('quantity')
        seating = request.POST.get('seating')
        color = request.POST.get('colors')

        category_id = request.POST.get('category')
        category = Category.objects.get(id=category_id)

        product.product_name = product_name
        product.material = material
        product.orginal_price = orginal_price
        product.offer_price = offer_price
        product.style = style
        product.description = description

        if image1:
            product.product_image1 = image1
        if image2:
            product.product_image2 = image2
        if image3:
            product.product_image3 = image3
        if image4:
            product.product_image4 = image4
        if image5:
            product.product_image5 = image5

        product.quantity = quantity
        product.seating = seating
        product.category = category
        product.colors = color

        
        if not (product_name and material and orginal_price and offer_price and style and description and
                image1 and image2 and image3 and image4 and image5 and quantity and seating and color):
            messages.error(request, 'Please provide all the required fields')
            return redirect('edit_products',p_id=p_id)

        try:
            orginal_price_str = request.POST.get('orginal_price')
            offer_price_str = request.POST.get('offer_price')
            orginal_price = int(orginal_price_str)
            offer_price = int(offer_price_str)
        except ValueError:
            messages.error(request, 'Orginal price and offer price must be valid numbers')
            return redirect('edit_products', p_id=p_id)

        if offer_price > orginal_price:
            messages.error(request, 'Offer price must be smaller than original price')
            return redirect('edit_products', p_id=p_id)

        if offer_price < 0 or orginal_price < 0:
            messages.error(request, 'Prices cannot be negative values')
            return redirect('edit_products', p_id=p_id)

        try:
            category = Category.objects.get(id=category_id, is_soft_delete=False)
        except Category.DoesNotExist:
            messages.error(request, 'Invalid category')
            return redirect('edit_products', p_id=p_id)

        product.save()

        return redirect('admin_product_list')

    return render(request, 'adminapp/edit_products.html', {'product': product, 'category_all': category_all})



def soft_delete_product(request, p_id):
    product = Products.objects.get(id=p_id)
    product.soft_delete_product()
    return redirect('admin_product_list')


def undo_soft_delete_product(request, p_id):
    product = Products.objects.get(id=p_id)
    product.soft_delete = False
    product.save()
    return redirect('admin_product_list')



def category(request):
    if not request.user.is_superuser:
        return render('admin_login')
    category_list=Category.objects.all().order_by('category_name')
    paginator=Paginator(category_list,5)


    if request.method =='POST':
        category_name=request.POST.get('category_name')
        category_image=request.FILES.get('category_image')
        category_description=request.POST.get('category_description')

        print(category_description,category_image,category_name)
        if not(category_description and category_name and category_image ):
            messages.error(request,'please provide all required fields.')
            return redirect('category')
        
        category=Category(
            category_name=category_name,
            category_image=category_image,
            category_desc=category_description,
        )
        category.save()
        print(category)

    try:
        page=int(request.GET.get('page',1))

    except:
        page=1

    try:
        categories=paginator.page(page)
    except(EmptyPage,InvalidPage):
        categories=paginator.page(paginator.num_pages)

    return render(request,'adminapp/category.html',{'categories':categories})

def edit_categories(request,c_id):
    if not request.user.is_superuser:
        return redirect('admin_login')
    category_list=Category.objects.all().order_by('category_name')
    paginator=Paginator(category_list,5)
    category=Category.objects.get(id=c_id)


    if request.method =='POST':
        category_name=request.POST.get('category_name')
        category_desc=request.POST.get('category_description')

        if 'category_image' in request.FILES:
            category_image=request.FILES.get('category_image')
            category.category_image=category_image

        category.category_name=category_name
        category.category_desc=category_desc

        category.save()

    try:
        page= int(request.GET.get('page',1))
    except:
        page=1

    try:
        catogries=paginator.page(page)
    except(EmptyPage,InvalidPage):
        catogries=paginator.page(paginator.num_pages)
    return render(request,'adminapp/edit_categories.html',{'catogries':catogries,'category':category})


def soft_delete(request, c_id):
    if request.method == 'POST':
        category = Category.objects.get(id=c_id)
        category.is_soft_delete = True
        category.save()
    return redirect('category')



def undo_soft_delete(request, c_id):
    if request.method == 'POST':
        category = Category.objects.get(id=c_id)
        category.is_soft_delete= False
        category.save()
    return redirect('category')

def orders(request):
    selected_status = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')

    if selected_status == 'all':
        orders_list = Order.objects.filter(is_ordered=True, user__username__icontains=search_query).order_by(
            '-created_at')
    else:
        orders_list = Order.objects.filter(is_ordered=True, status=selected_status,
                                           user__username__icontains=search_query).order_by('-created_at')

    paginator = Paginator(orders_list, 10)

    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1

    try:
        orders = paginator.page(page)
    except (EmptyPage, InvalidPage):
        orders = paginator.page(paginator.num_pages)

    context = {
        'orders': orders,
        'selected_status': selected_status,
        'search_query': search_query,
    }
    return render(request,'adminapp/orders.html',context)


def order_details(request, order_id):
    order = Order.objects.get(id=order_id, is_ordered=True)  
    
    order_products = OrderProduct.objects.filter(order=order)
    print(order_products)

    for order_product in order_products:
        order_product.total = order_product.quantity * order_product.product.offer_price
        order_product.tax = (8 * order_product.total) / 100
        order_product.stotal = order_product.total + order_product.tax

    context = {
        'order': order,
        'order_products': order_products,
    }

    return render(request, 'adminapp/order_details.html', context)



def update_order_status(request, order_id, new_status):
    order = Order.objects.get(id=order_id, is_ordered=True)
    order_products = OrderProduct.objects.filter(order=order)

    if new_status == 'New':
        order.status = 'New'
    elif new_status == 'Cancelled':
        order.status = 'Cancelled'
        payment_methods = Payment.objects.filter(orderproduct__order=order).values_list('payment_method', flat=True)
        if 'Wallet' in payment_methods or 'Razor pay' in payment_methods:
            user_wallet, created = Wallet.objects.get_or_create(user=order.user)
            user_wallet.amount += order.order_total
            user_wallet.save()

            for order_product in order.orderproduct_set.all():
                product = order_product.product
                product.quantity += order_product.quantity  # Increase the quantity
                product.save()

    elif new_status == 'Delivered':
        for order_product in order_products:
            if order_product.payment.payment_method == 'Cash on delivery' and order_product.payment.status == 'Not Paid':
                order_product.payment.status = 'Paid'
                order_product.payment.save()
        order.status = new_status
        order.save()

    elif new_status == 'Returned':
        for order_product in order_products:
            if order_product.payment.payment_method == 'Cash on delivery' and order_product.payment.status == 'Not Paid':
                order_product.payment.status = 'Paid'
                order_product.payment.save()
        order.status = new_status
        order.save()
        order.status = new_status
        payments = Payment.objects.filter(orderproduct__order=order, payment_method__in=['Razor pay', 'Wallet'])
        for payment in payments:
            user_wallet, created = Wallet.objects.get_or_create(user=order.user)
            user_wallet.amount += order.order_total
            user_wallet.save()

        for order_product in order.orderproduct_set.all():
            product = order_product.product
            product.quantity += order_product.quantity  # Increase the quantity
            product.save()

    order.save()
    return redirect('order_details', order_id=order_id)

def sales(request):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    total_sales = Order.objects.filter(status='Delivered', created_at__range=(start_date, end_date)).aggregate(
        total_sales=Sum('order_total'))['total_sales'] or 0

    total_orders = Order.objects.filter(created_at__range=(start_date, end_date)).count()
    success_orders = Order.objects.filter(status='Delivered', created_at__range=(start_date, end_date)).count()
    average_order_value = total_sales / success_orders if success_orders != 0 else 0
    delivered_products = OrderProduct.objects.filter(order__status='Delivered',
                                                     order__created_at__range=(start_date, end_date), ordered=True
                                                     ).values('product__product_name'
                                                              ).annotate(total_quantity_sold=Sum('quantity'),
                                                                         total_revenue=Sum(
                                                                             F('quantity') * F('product_price'))
                                                                         # Calculate total revenue here using F expressions
                                                                         ).order_by('-total_quantity_sold')

    order_products = Order.objects.filter(status='Delivered', created_at__range=(start_date, end_date)).order_by(
        '-created_at')
    Month = end_date.month
    print(Month)

    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'average_order_value': average_order_value,
        'delivered_products': delivered_products,
        'end_date': end_date,
        'order_products': order_products,
        'success_orders': success_orders,
        'month': Month
    }

    return render(request, 'adminapp/sales.html', context)

def today_sales(request):
    current_datetime = datetime.now()
    current_day = current_datetime.strftime('%d')

    start_date = datetime.combine(current_datetime.date(), time.min)
    end_date = current_datetime

    total_sales = Order.objects.filter(status='Delivered', created_at__range=(start_date, end_date)).aggregate(
        total_sales=Sum('order_total'))['total_sales'] or 0
    total_orders = Order.objects.filter(created_at__range=(start_date, end_date)).count()
    success_orders = Order.objects.filter(status='Delivered', created_at__range=(start_date, end_date)).count()
    average_order_value = total_sales / success_orders if success_orders != 0 else 0

    delivered_products = OrderProduct.objects.filter(order__status='Delivered',
                                                     order__created_at__range=(start_date, end_date), ordered=True
                                                     ).values('product__product_name'
                                                              ).annotate(total_quantity_sold=Sum('quantity'),
                                                                         total_revenue=Sum(
                                                                             F('quantity') * F('product_price'))
                                                                         ).order_by('-total_quantity_sold')

    order_products = Order.objects.filter(status='Delivered', created_at__range=(start_date, end_date)).order_by(
        '-created_at')

    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'success_orders': success_orders,
        'average_order_value': average_order_value,
        'delivered_products': delivered_products,
        'current_datetime': current_datetime,
        'current_day': current_day,
        'order_products': order_products,
    }
    return render(request, 'adminapp/today_sales.html', context)

def current_year_sales(request):
    current_year = datetime.now().year
    start_date = datetime(current_year, 1, 1)
    end_date = datetime.now()

    total_sales = Order.objects.filter(status='Delivered', created_at__range=(start_date, end_date)
                                       ).aggregate(total_sales=Sum('order_total'))['total_sales'] or 0

    total_orders = Order.objects.filter(created_at__range=(start_date, end_date)).count()
    success_orders = Order.objects.filter(status='Delivered', created_at__range=(start_date, end_date)).count()
    average_order_value = total_sales / success_orders if success_orders != 0 else 0

    delivered_products = OrderProduct.objects.filter(order__status='Delivered',
                                                     order__created_at__range=(start_date, end_date),
                                                     ).values('product__product_name'
                                                              ).annotate(total_quantity_sold=Sum('quantity'),
                                                                         total_revenue=Sum(
                                                                             F('quantity') * F('product_price'))
                                                                         # Calculate total revenue using F expressions
                                                                         ).order_by('-total_quantity_sold')

    order_products = Order.objects.filter(status='Delivered', created_at__range=(start_date, end_date)).order_by(
        '-created_at')

    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'success_orders': success_orders,
        'average_order_value': average_order_value,
        'delivered_products': delivered_products,
        'current_year': current_year,
        'order_products': order_products,
    }

    return render(request, 'adminapp/current_year_sales.html', context)
 

def banner(request):
    if not request.user.is_superuser:
        return redirect('admin_login')

    banners = Banner.objects.all()

    if request.method == 'POST':
        banner_image = request.FILES.get('image')  
        title = request.POST.get('title')  
        subtitle = request.POST.get('sub_title')  

        if not all([banner_image, title, subtitle]):
            messages.error(request, 'Please provide all the required fields')
        else:
            banner = Banner(
                banner_img=banner_image,
                title=title,
                subtitle=subtitle
            )
            banner.save()
            # Redirect after successful form submission
            return redirect('banner')

    context = {
        'banners': banners
    }

    return render(request, 'adminapp/banner.html', context)

def edit_banner(request, banner_id):
    banner = Banner.objects.get(id=banner_id)

    if request.method == 'POST':
        banner_img = request.FILES.get('image')
        title = request.POST.get('title')
        subtitle = request.POST.get('sub_title')

        if not all([banner_img, title, subtitle]):
            messages.error(request, 'Please provide all the required fields.')
        else:
            banner.banner_img = banner_img
            banner.title = title
            banner.subtitle = subtitle
            banner.save()

            messages.success(request, 'Banner updated successfully.')
            return redirect('banner')  

    context = {
        'banner': banner,
    }

    return render(request, 'adminapp/edit_banner.html', context)

def coupon(request):

    search_query = request.GET.get('search')
    coupons = Coupons.objects.all().order_by('-valid_to')
    if search_query:
        coupons = coupons.filter(Q(coupon_code__icontains=search_query))
    context = {'coupons': coupons}
    return render(request,'adminapp/coupon.html',context)

def add_coupon(request):

    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        description = request.POST.get('description')
        minimum_amount = request.POST.get('minimum_amount')
        discount = request.POST.get('discount')
        valid_from = request.POST.get('valid_from')
        valid_to = request.POST.get('valid_to')

        # Check for empty fields
        if not (coupon_code and description and minimum_amount and discount and valid_from and valid_to):
            messages.error(request, "All fields are required.")
            return redirect('add_coupon')

        try:
            minimum_amount = int(minimum_amount)
            discount = int(discount)
        except ValueError:
            messages.error(request, "Minimum Amount and Discount must be integers.")
            return redirect('add_coupon')

        # Check if discount is greater than minimum amount
        if discount > minimum_amount:
            messages.error(request, "Discount cannot be greater than Minimum Amount.")
            return redirect('add_coupon')

        if valid_from > valid_to:
            messages.error(request, "Valid From date should not be greater than Valid To date.")
            return redirect('add_coupon')

        coupon = Coupons(
            coupon_code=coupon_code,
            description=description,
            minimum_amount=minimum_amount,
            discount=discount,
            valid_from=valid_from,
            valid_to=valid_to
        )
        coupon.save()
        messages.success(request, "Coupon added successfully.")
        return redirect('coupon')


    return render(request,'adminapp/add_coupon.html')

@login_required
def edit_coupons(request, coupon_id):
    try:
        coupon = Coupons.objects.get(pk=coupon_id)
    except Coupons.DoesNotExist:
        return redirect('admin_coupons')

    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        description = request.POST.get('description')
        minimum_amount = request.POST.get('minimum_amount')
        discount = request.POST.get('discount')
        valid_from = request.POST.get('valid_from')
        valid_to = request.POST.get('valid_to')

        # Check for empty fields
        if not (coupon_code and description and minimum_amount and discount and valid_from and valid_to):
            messages.error(request, "All fields are required.")
            return redirect('edit_coupons', coupon_id=coupon_id)

        try:
            minimum_amount = int(minimum_amount)
            discount = int(discount)
        except ValueError:
            messages.error(request, "Minimum Amount and Discount must be integers.")
            return redirect('edit_coupons', coupon_id=coupon_id)

        # Check if discount is greater than minimum amount
        if discount > minimum_amount:
            messages.error(request, "Discount cannot be greater than Minimum Amount.")
            return redirect('edit_coupons', coupon_id=coupon_id)

        if valid_from > valid_to:
            messages.error(request, "Valid From date should not be greater than Valid To date.")
            return redirect('edit_coupons', coupon_id=coupon_id)

        coupon.coupon_code = coupon_code
        coupon.description = description
        coupon.minimum_amount = minimum_amount
        coupon.discount = discount
        coupon.valid_from = valid_from
        coupon.valid_to = valid_to

        coupon.save()

        return redirect('coupon')

    context = {'coupon': coupon}
    return render(request, 'adminapp/edit_coupon.html', context)


def list_coupon(request, c_id):
    coupon = Coupons.objects.get(id=c_id)
    coupon.un_list = False
    coupon.save()
    return redirect('coupon')


def unlist_coupon(request, c_id):
    coupon = Coupons.objects.get(id=c_id)
    coupon.un_list = True
    coupon.save()
    return redirect('coupon')


def coupon_details(request, coupon_id):
    coupon = get_object_or_404(Coupons, id=coupon_id)
    used_users = UserCoupons.objects.filter(coupon=coupon)
    is_expired = coupon.valid_to < timezone.now()
    context = {
        'coupon': coupon,
        'used_users': used_users,
        'is_expired': is_expired,
    }

    return render(request, 'adminapp/coupon_details.html', context)

def admin_logout(request):
    request.session.flush()
    logout(request)
    return redirect('admin_login')