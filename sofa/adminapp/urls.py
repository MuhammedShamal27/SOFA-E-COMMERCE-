from django.urls import path
from . import views


urlpatterns = [
    path('admin_home/',views.admin_home,name='admin_home'),
    path('admin_login/',views.admin_login,name='admin_login'),

    path('customer/',views.customer,name='customer'),
    path('block_user/<int:u_id>/',views.block_user,name='block_user'),
    path('unblock_user/<int:u_id>/', views.unblock_user, name='unblock_user'),

    path('category/',views.category,name='category'),
    path('edit_categories/<int:c_id>/',views.edit_categories,name='edit_categories'),
    path('soft_delete/<int:c_id>/',views.soft_delete,name='soft_delete'),
    path('undo_soft_delete/<int:c_id>/',views.undo_soft_delete,name='undo_soft_delete'),
    
    # path('process_image/', views.process_image, name='process_image'),
    path('add_product/',views.add_product,name='add_product'),
    path('admin_product_list/',views.admin_product_list,name='admin_product_list'),
    path('edit_products/<int:p_id>/',views.edit_products,name='edit_products'),
    path('soft_delete_product/<int:p_id>/',views.soft_delete_product,name='soft_delete_product'),
    path('undo_soft_delete_product/<int:p_id>/',views.undo_soft_delete_product,name='undo_soft_delete_product'),

    path('orders/',views.orders,name='orders'),
    path('order_details/<int:order_id>',views.order_details,name='order_details'),
    path('update_order_status/<int:order_id>/<str:new_status>/', views.update_order_status, name='update_order_status'),

    path('sales/',views.sales,name='sales'),
    path('today_sales/',views.today_sales,name='today_sales'),
    path('current_year_sales/',views.current_year_sales,name='current_year_sales'),   

    path('banner/',views.banner,name='banner'),
    path('edit_banner/<int:banner_id>/', views.edit_banner, name='edit_banner'),

    path('coupon/',views.coupon,name='coupon'),
    path('add_coupon/',views.add_coupon,name='add_coupon'),
    path('edit_coupons/<int:coupon_id>/', views.edit_coupons, name='edit_coupons'),
    path('unlist_coupon/<int:c_id>/', views.unlist_coupon, name='unlist_coupon'),
    path('list_coupon/<int:c_id>/', views.list_coupon, name='list_coupon'),
    path('coupon_details/<int:coupon_id>/', views.coupon_details, name='coupon_details'),

    path('admin_logout/',views.admin_logout,name='admin_logout'),
]