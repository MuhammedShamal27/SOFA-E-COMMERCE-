from django.shortcuts import render,redirect
from .models import *
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.db import transaction
import uuid
import datetime
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from adminapp.models import *

# Create your views here.
def cart_id(request):
    if request.user.is_authenticated:
        return f"user_{request.user.id}"
    else:
        cart_id = request.session.session_key
        if not cart_id:
            cart_id = request.session.create()
        return cart_id


def add_to_cart_from_wishlist(request, wishlist_item_id):
    wishlist_item = get_object_or_404(Wishlist, id=wishlist_item_id)
    product = wishlist_item.product

    c_user = request.user
    cart_item = None

    try:
        cart = Cart.objects.get(cart_id=cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(cart_id=cart_id(request), user=c_user)

    try:
        cart_item = Cartitem.objects.get(user=c_user, product=product, cart=cart)
        if cart_item.quantity + 1 <= product.quantity:
            cart_item.quantity += 1
            cart_item.save()
    except Cartitem.DoesNotExist:
        if cart_item is None:  
            # Create a new Cartitem if it was not found
            cart_item = Cartitem.objects.create(
                product=product,
                quantity=1,
                user=c_user,
                cart=cart,
            )

    total = cart_item.quantity * product.offer_price
    quantity = cart_item.quantity
    sub_total = cart_item.sub_total()

    # Calculate the grandTotal by summing up subtotals of all cart items
    grandTotal = sum(item.sub_total() for item in cart.cartitem_set.all())

    try:
        # Your existing code...

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'item_id': cart_item.id,
                'quantity': quantity,
                'total': total,
                'sub_total': sub_total,
                'grandTotal': grandTotal,
            })

    except Exception as e:
        # Log the error or print it for debugging purposes
        print(f"Error in add_to_cart_from_wishlist: {e}")

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'An error occurred while processing the request'}, status=500)

    return redirect('user_cart')



def add_to_cart(request, product_id):
    c_user = request.user
    product = get_object_or_404(Products, id=product_id)

    
    try:
        cart = Cart.objects.get(cart_id=cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id=cart_id(request),
            user=c_user,
        )
        cart.save()

    try:
        cart_item = Cartitem.objects.get(user=c_user, product=product, cart=cart)
        cart_item.quantity += 1
        cart_item.save()
        print(cart_item.quantity)
    except Cartitem.DoesNotExist:
        cart_item = Cartitem.objects.create(
            product=product,
            quantity=1,
            user=c_user,
            cart=cart,
        )
        cart_item.save()

    total = cart_item.quantity * product.offer_price
    quantity = cart_item.quantity
    sub_total = cart_item.sub_total()  # Assuming you have a method named sub_total in your Cartitem model

    # Calculate the grandTotal by summing up subtotals of all cart items
    grandTotal = sum(item.sub_total() for item in cart.cartitem_set.all())

    try:
        # Your existing code...

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'item_id': cart_item.id,
                'quantity': quantity,
                'total': total,
                'sub_total': sub_total,
                'grandTotal': grandTotal,
            })

    except Exception as e:
        # Log the error or print it for debugging purposes
        print(f"Error in add_to_cart: {e}")

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'An error occurred while processing the request'}, status=500)

    return redirect('user_cart')




def user_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(cart_id=cart_id(request), user=request.user)
        cart_items = Cartitem.objects.filter(user=request.user, cart=cart, is_active=True)

        total, quantity,grandTotal = calculate_cart_total_and_quantity(cart)
        print(grandTotal)

        context = {
            'total': total,
            'quantity': quantity,
            'cart_items': cart_items,
            'grandTotal': grandTotal
        }
    else:
    
        context = {
            'total': 0,
            'quantity': 0,
            'cart_items': []
        }

    return render(request, 'cart/user_cart.html', context)


def calculate_cart_total_and_quantity(cart):
    total = 0
    quantity = 0

    cart_items = Cartitem.objects.filter(cart=cart, is_active=True)

    for cart_item in cart_items:
        try:
            offer_price_int = int(cart_item.product.offer_price)
        except ValueError:
            offer_price_int = 0.0

        total += (offer_price_int * cart_item.quantity)
        quantity += cart_item.quantity

    grandTotal = total  # Set grand total as the sum of totals for all items
    return total, quantity, grandTotal


def remove_product(request, product_id):
    cart = Cart.objects.get(cart_id=cart_id(request))
    product = get_object_or_404(Products, id=product_id)

    try:
        cart_item = Cartitem.objects.get(product=product, cart=cart)

        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()

        total = cart_item.quantity * product.offer_price
        quantity=cart_item.quantity
        sub_total = cart_item.sub_total()

        grandTotal = sum(item.sub_total() for item in cart.cartitem_set.all())

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'item_id': cart_item.id, 'quantity': quantity, 'total': total,'sub_total': sub_total,'grandTotal': grandTotal})

    except Cartitem.DoesNotExist:
        pass
    except Exception as e:
        # Log the error or print it for debugging purposes
        print(f"Error in remove_product: {e}")

    return redirect('user_cart')




def remove_cart(request,product_id):

    product = Products.objects.get(id=product_id)

    try:
        cart_item = Cartitem.objects.get(product=product, cart__cart_id=cart_id(request))
        cart_item.delete()
        
    except :
       pass

    return redirect('user_cart')


def checkout(request, total=0, quantity=0, cart_items=None):
    tax=shipping=grand_total=0
   
    user = request.user
    try:
        tax = 0
        shipping = 0
        grand_total = 0

        if request.user.is_authenticated:
            cart_items = Cartitem.objects.filter(user=request.user, is_active=True,product__soft_delete=False)
        else:
            cart = Cart.objects.get(cart_id=cart_id(request))
            cart_items = Cartitem.objects.filter(cart=cart, is_active=True,product__soft_delete=False)

        for cart_item in cart_items:
            total += cart_item.product.offer_price* cart_item.quantity
            quantity += cart_item.quantity


        tax = (18 * total) / 100
        shipping = 0
        grand_total = total + tax
    except Cart.DoesNotExist:
        pass
    except Cartitem.DoesNotExist:
        pass

    if cart_items.count() == 0:
        return redirect('user_cart')

    address_list = Address.objects.filter(user=request.user)
    sorted_addresses = sorted(address_list, key=lambda x: not x.is_default)

    context = {
        'user': user,
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'shipping': shipping,
        'grand_total': grand_total,
        'address_list': sorted_addresses,
    }
    return render(request, 'cart/checkout.html', context)

def checkout_address(request, user_id):
    user = User.objects.get(id=user_id)
    address_list = Address.objects.filter(user=request.user)
    sorted_addresses = sorted(address_list, key=lambda x: not x.is_default)

    if request.method == 'POST':
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

        if not all([first_name, last_name, email, paddress, phone, locality, city, state, landmark, pincode]):
            messages.error(request, 'All fields are required.')
            return redirect('checkout')

        if not is_valid_phone(phone):
            messages.error(request, 'Invalid phone number. Please enter a 10-digit numeric phone number.')
            return redirect('checkout')

        address = Address(
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

        return redirect('checkout')

    context = {
        'user': user,
        'address': sorted_addresses,
    }
    return redirect('checkout')

def is_valid_phone(phone):
    return phone.isdigit() and len(phone) == 10



def place_order(request):
    if not request.user.is_authenticated:
        return redirect('signin')

    current_user = request.user

    cart_items = Cartitem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('product_list')

    total = 0  # Initialize total
    quantity = 0  # Initialize quantity

    discount = 0
    grand_total = 0
    

    for cart_item in cart_items:
        total += (cart_item.product.offer_price * cart_item.quantity)
        quantity += cart_item.quantity

    
    grand_total = total 

    if request.method == 'POST':
        address_id = request.POST.get('default_address')

        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            messages.warning(request, "Select an address.")
            return redirect('user_cart')

        data = Order()
        data.user = current_user
        data.address = address
        data.order_total = grand_total
        data.save()

        yr = int(datetime.date.today().strftime('%Y'))
        dt = int(datetime.date.today().strftime('%d'))
        mt = int(datetime.date.today().strftime('%m'))
        d = datetime.date(yr, mt, dt)
        current_date = d.strftime("%Y%m%d")

        order_number = current_date + str(data.id)
        print(order_number)
        data.order_number = order_number
        data.save()

        order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
        context = {
            'order': order,
            'cart_items': cart_items,
            'total': total,
            'grand_total': grand_total,
            'discount': discount,
            'address': address
        }

        return redirect('payments', order_id=order.id)
    else:
        return redirect('checkout')
    
from django.utils import timezone

def apply_coupon(request):
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        order_id = request.POST.get('order_id')
        request.session['coupon_code'] = coupon_code

        try:
            coupon = Coupons.objects.get(coupon_code=coupon_code, un_list=False)
            order = Order.objects.get(id=order_id)

            if coupon.valid_from <= timezone.now() <= coupon.valid_to:
                if order.order_total >= coupon.minimum_amount:
                    if coupon.is_used_by_user(request.user):
                        messages.warning(request, 'Coupon has already been Used')
                        print('Coupon has already been Used')
                    else:
                        updated_total = order.order_total - float(coupon.discount)
                        order.order_total = updated_total
                        order.discount = float(coupon.discount)
                        order.save()

                        # used_coupons = UserCoupons(user=request.user, coupon=coupon, is_used=True)
                        # used_coupons.save()

                        request.session['coupon_discount'] = float(coupon.discount)
                        request.session['applied_coupon_code'] = coupon.coupon_code
                        messages.success(request, 'Coupon successfully added')
                        return redirect('payments', order_id)
                else:
                    messages.warning(request, 'Coupon is not Applicable for Order Total')
            else:
                messages.warning(request, 'Coupon is not Applicable for the current date')
        except ObjectDoesNotExist:
            messages.warning(request, 'Coupon code is Invalid')
            return redirect('payments', order_id)

    return redirect('payments', order_id)

def payments(request, order_id):

    current_user = request.user
    cart_items = Cartitem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    order = Order.objects.get(user=current_user, is_ordered=False, id=order_id)
    if cart_count <= 0:
        return redirect('product_list')

    
    grand_total = order.order_total
    total = 0
    quantity = 0
    sub_total = 0



    for cart_item in cart_items:
        total += (cart_item.product.offer_price * cart_item.quantity)
        quantity += cart_item.quantity
        sub_total += cart_item.sub_total()




    try:
        address = order.address
    except Order.DoesNotExist:
        return redirect('payments')

    context = {
        'address': address,
        'order': order,
        'cart_items': cart_items,
        'total': total,
        'sub_total': sub_total,
        'grand_total': grand_total,
    }
    return render(request, 'cart/place_order.html', context)
@transaction.atomic
def cash_on_delivery(request, order_id):
    current_user = request.user
    try:
        order = Order.objects.get(id=order_id, user=current_user, is_ordered=False)
    except Order.DoesNotExist:
        return redirect('order_confirmed')

    total_amount = order.order_total

    payment = Payment(user=current_user, payment_method="Cash on delivery", amount_paid=total_amount, status="Not Paid")

    payment.save()
    order.is_ordered = True
    order.payment = payment
    order.save()
    cart_items = Cartitem.objects.filter(user=current_user)

    for cart_item in cart_items: 
        product = cart_item.product
        stock = product.quantity - cart_item.quantity
        product.quantity = stock
        product.save()
        order_product = OrderProduct(
            order=order,
            payment=payment,
            user=current_user,
            product=cart_item.product,
            quantity=cart_item.quantity,
            product_price=cart_item.product.offer_price,
            ordered=True,
        )
        order_product.save()
    cart_items.delete()
    order_products = OrderProduct.objects.filter(order=order)
    wishlist_items = Wishlist.objects.filter(user=current_user, product__in=[order_product.product for order_product in
                                                                     order_products])
    wishlist_items.delete()

    applied_coupon_code = request.session.get('coupon_code')
    if applied_coupon_code:
        try:
            coupon = Coupons.objects.get(coupon_code=applied_coupon_code)
            used_coupons = UserCoupons(user=request.user, coupon=coupon, is_used=True)
            used_coupons.save()
        except Coupons.DoesNotExist:
            pass

    if 'coupon_discount' in request.session:
        del request.session['coupon_discount']
    
    return redirect('order_confirmed', order_id=order_id)

@transaction.atomic
def confirm_razorpay_payment(request, order_id):
    current_user = request.user
    try:
        order = Order.objects.get(id=order_id, user=current_user, is_ordered=False)
    except Order.DoesNotExist:
        return redirect('order_confirmed')

    total_amount = order.order_total

    payment = Payment(user=current_user, payment_method="Razor pay", amount_paid=total_amount, status="Paid")
    payment.save()
    order.is_ordered = True
    order.payment = payment
    order.save()

    cart_items = Cartitem.objects.filter(user=current_user)

    for cart_item in cart_items:
        product = cart_item.product
        stock = product.quantity - cart_item.quantity
        product.quantity = stock
        product.save()
        order_product = OrderProduct(
            order=order,
            payment=payment,
            user=current_user,
            product=cart_item.product,
            quantity=cart_item.quantity,
            product_price=cart_item.product.offer_price,
            ordered=True,
        )
        order_product.save()
    cart_items.delete()
    order_products = OrderProduct.objects.filter(order=order)
    wishlist_items = Wishlist.objects.filter(user=current_user, product__in=[order_product.product for order_product in
                                                                     order_products])
    wishlist_items.delete()

    applied_coupon_code = request.session.get('coupon_code')
    if applied_coupon_code:
        try:
            coupon = Coupons.objects.get(coupon_code=applied_coupon_code)
            used_coupons = UserCoupons(user=request.user, coupon=coupon, is_used=True)
            used_coupons.save()
        except Coupons.DoesNotExist:
            pass

    if 'coupon_discount' in request.session:
        del request.session['coupon_discount']

    
    return redirect('order_confirmed', order_id=order_id)


@transaction.atomic
def wallet_pay(request, order_id):
    user = request.user
    order = Order.objects.get(id=order_id)
    try:
        wallet = Wallet.objects.get(user=user)

    except:
        wallet = Wallet.objects.create(user=user, amount=0)
        wallet.save()

    if wallet.amount > order.order_total:
        payment = Payment.objects.create(user=user, payment_method='Wallet', amount_paid=order.order_total,
                                         status='Paid')
        payment.save()
        order.is_ordered = True

        order.payment = payment
        order.save()
        wallet.amount -= order.order_total
        wallet.save()

        cart_items = Cartitem.objects.filter(user=user)

        for cart_item in cart_items:
            
            order_product = OrderProduct(
                order=order,
                payment=payment,
                user=user,
                product=cart_item.product,
                quantity=cart_item.quantity,
                product_price=cart_item.product.offer_price,
                ordered=True,

            )
            order_product.save()

        cart_items.delete()
        order_products = OrderProduct.objects.filter(order=order)
        wishlist_items = Wishlist.objects.filter(user=user, product__in=[order_product.product for order_product in
                                                                         order_products])
        wishlist_items.delete()



    else:
        messages.warning(request, 'Not Enough Balance in Wallet')
        return redirect('payments', order_id)
    
    applied_coupon_code = request.session.get('coupon_code')
    if applied_coupon_code:
        try:
            coupon = Coupons.objects.get(coupon_code=applied_coupon_code)
            used_coupons = UserCoupons(user=request.user, coupon=coupon, is_used=True)
            used_coupons.save()
        except Coupons.DoesNotExist:
            pass


    
    return redirect('order_confirmed', order_id=order_id)


def order_confirmed(request,order_id):
 
    order_products = OrderProduct.objects.filter(order__user=request.user, order__id=order_id)
    orders = Order.objects.filter(is_ordered=True, id=order_id)
    
    total_amount = 0


    for order_product in order_products:
        order_product.total = order_product.quantity * order_product.product_price
        total_amount += order_product.total
    

    payments = Payment.objects.filter(orderproduct__order__id=order_id)[:1]

    order = orders.first()
        
    context = {
        'order_products': order_products,
        'orders': orders,
        'payments': payments,
        'address': order.address,
        'total_amount': total_amount,
    }

    return render(request,'cart/order_confirmed.html',context)
