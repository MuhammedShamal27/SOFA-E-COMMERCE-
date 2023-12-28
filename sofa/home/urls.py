from django.urls import path
from . import views


urlpatterns = [
    path('',views.index,name='index'),

    path('product_list/',views.product_list,name='product_list'),
    path('product_detail/<int:p_id>/',views.product_detail,name='product_detail'),

    path('user_profile/',views.user_profile,name='user_profile'),
    path('profile/<int:user_id>/',views.profile,name='profile'),
    path('edit_user/<int:user_id>/',views.edit_user,name='edit_user'),
    path('user_address/<int:user_id>/',views.user_address,name='user_address'),
    path('user_order/',views.user_order,name='user_order'),
    path('user_order_view/<int:order_id>/',views.user_order_view,name='user_order_view'),
    path('cancel_order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('return_order/<int:order_id>/', views.return_order, name='return_order'),
    path('user_wallet/',views.user_wallet,name='user_wallet'),
    
    path('wishlist/<int:product_id>/',views.wishlist,name='wishlist'),
    path('user_wishlist/<int:user_id>/',views.user_wishlist,name='user_wishlist'),
    path('remove_user_wishlist/<int:product_id>/',views.remove_user_wishlist,name='remove_user_wishlist'),

    path('user_coupon/',views.user_coupon,name='user_coupon'),
    
]