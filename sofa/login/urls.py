from django.urls import path
from . import views


urlpatterns = [
    path('signin/',views.signin,name='signin'),
    path('register/',views.register,name='register'),  
    path('otp_page/',views.otp_page,name='otp_page'),
    path('sent_otp/',views.send_otp,name='sent_otp'),
    path('verify_otp/',views.verify_otp,name='verify_otp'),
    path('resend_otp/', views.resend_otp, name='resend_otp'),  
    path('forgot_password/',views.forgot_password,name='forgot_password'),
    path('confirm_password/',views.confirm_password,name='confirm_password'),
    path('profile_forget_password/<int:user_id>/',views.profile_forget_password,name='profile_forget_password'),
    path('confrim_password/',views.profile_confrim_password,name='profile_confrim_password'),   
    path('logout/',views.Logout,name='logout'),
]
