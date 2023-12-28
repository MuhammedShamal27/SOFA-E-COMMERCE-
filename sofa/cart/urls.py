from django.urls import path
from . import views


urlpatterns = [
    path('cart_id/',views.cart_id,name='cart_id'),
    path('user_cart/',views.user_cart,name='user_cart'),
    path('add_to_cart/<int:product_id>/',views.add_to_cart,name='add_to_cart'),
    path('add_to_cart_from_wishlist/<int:wishlist_item_id>/',views.add_to_cart_from_wishlist, name='add_to_cart_from_wishlist'),
    path('remove_product/<int:product_id>/',views.remove_product,name='remove_product'),
    path('remove_cart/<int:product_id>/',views.remove_cart,name='remove_cart'),
    path('calculate_cart_total_and_quantity/',views.calculate_cart_total_and_quantity,name='calculate_cart_total_and_quantity'),
    

    path('checkout/',views.checkout,name='checkout'),
    path('checkout_address/<int:user_id>/',views.checkout_address,name='checkout_address'),

    path('place_order/',views.place_order,name='place_order'),
    path('payments/<int:order_id>/',views.payments,name='payments'),
    path('apply_coupon/',views.apply_coupon,name='apply_coupon'),
    path('cash_on_delivery/<int:order_id>/',views.cash_on_delivery,name='cash_on_delivery'),
    path('confirm_razorpay_payment/<int:order_id>/',views.confirm_razorpay_payment,name='confirm_razorpay_payment'),
    path('wallet_pay/<int:order_id>/',views.wallet_pay,name='wallet_pay'),
    path('order_confirmed/<int:order_id>/',views.order_confirmed,name='order_confirmed'),


   
]