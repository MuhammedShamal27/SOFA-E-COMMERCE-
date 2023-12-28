from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
import random
from django.views.decorators.cache import never_cache


# Create your views here.
@never_cache
def signin(request):
    if 'username' in request.session:
        return redirect('/')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        request.session['email'] = email
        request.session['password'] = password

        if not email and not password:
            messages.warning(request, 'Enter details to field')
            return redirect('signin')
       
        user = authenticate(request, username=email, password=password)
        print(user,email,password)
        
        if user is not None and user.is_active:
            request.session['verification_type'] = 'signin'
            send_otp(request)
            return redirect('otp_page')
        else:
            messages.error(request, 'Invalid username or password')
            return redirect('signin')

    return render(request,'login/signin.html')


def register(request):


    if request.method=='POST':
        username=request.POST.get('username')
        email=request.POST.get('email')
        password=request.POST.get('password')
        confrim_password=request.POST.get('confirm_password')

        request.session['uname'] = username
        request.session['email'] = email
        request.session['password'] = password



        try:
            if not username or  not email or not password:
                messages.error(request, 'Enter details to field')
                return redirect('register')
        except:
            pass

        try:
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists. Please choose a different one.")
                return redirect("register")
            elif not username.isalnum():
                messages.warning(request, "Username contains invalid characters. Please use only letters and numbers.")
                return redirect("register")
        except:
            pass

        try:
            if User.objects.filter(email=email):
                messages.error(request, "Email already exists")
                return redirect("register")
        except:
            pass

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Invalid email address")
            return redirect('register')

        try:
            if password !=confrim_password:
                messages.error(request, "passwords not matching")
                return redirect("register")
        except:
            pass

        try:
            if len(username)>20:
                messages.error(request, "username is too long")
                return redirect("register")
        except:
            pass

        try:
            if len(password)<8:
                messages.error(request, "Password must be at least 8 characters")
                return redirect("register")
        except:
            pass

        request.session['verification_type'] = 'register'
        send_otp(request)
        return render(request, 'login/verify_otp.html', {"email": email})


    return render(request,'login/register.html')


def otp_page(request):
    if 'username' in request.session:
        return redirect('/')
    email=request.session['email']
    return render(request,'login/verify_otp.html',{'email':email})



def send_otp(request):
    s = ""
    for x in range(0, 4):
        s += str(random.randint(0, 9))
    print(s)
    request.session["otp"] = s
    email = request.session.get('email')

    send_mail("otp for sign up", s, 'muhammedshamalps10@gmail.com', [email], fail_silently=False)
    return render(request, "login/verify_otp.html", {"email": email})


def verify_otp(request):
    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        otp_sent = request.session.get('otp')
        verification_type = request.session.get('verification_type')

        if otp_entered == otp_sent:
            username = request.session.get('uname')
            email = request.session.get('email')
            password = request.session.get('password')
            print()
            print(email,password)

            if verification_type == 'register':
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()

                return redirect(signin)
                # messages.success(request, "Registration successful. You can now log in.")

            elif verification_type == 'signin':
                user = authenticate(request, username=email, password=password)
                print(user)
                if user is not None :
                    username = user.username
                    request.session['username'] = username
                    login(request, user)
                    return redirect('/')
                else:
                    messages.error(request, 'Invalid credentials')
                    return redirect('signin')
           
            elif verification_type == 'forgot_password':
                return redirect('confirm_password')
            
            elif verification_type == 'profile_forget_password':
                return redirect('profile_confrim_password')

            request.session.clear()
            return redirect('signin')
        else:
            messages.error(request, "Invalid OTP. Please try again.")
            return render(request, 'login/verify_otp.html', {"email": request.session.get('email')})

    return render(request, 'login/signin.html')


def resend_otp(request):
    new_otp = "".join([str(random.randint(0, 9)) for _ in range(4)])
    print(new_otp)
    email = request.session.get('email')
    send_mail("New OTP for Sign Up", new_otp, 'muhammedshamalps10@gmail.com', [email], fail_silently=False)
    request.session['otp'] = new_otp
    return redirect('otp_page')

def forgot_password(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == "POST":
        email = request.POST['email']
        if User.objects.filter(email=email).exists():
            request.session['verification_type'] = 'forgot_password'
            request.session['email'] = email
            send_otp(request)
            return redirect('otp_page')
        else:
            messages.error(request, 'Email not registered')

    return render(request,'login/forgot_password.html')

from django.contrib.auth import authenticate, login

def confirm_password(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == "POST":
        password = request.POST.get('password1')
        confirm_password = request.POST.get('password2')

        print(password)
        if password == confirm_password:
            email = request.session.get('email')
            print(email)
            user = User.objects.get(email=email)
            print(user)
            user.set_password(password)  # to change the password
            user.save()
            print('set')


            authenticated_user = authenticate(request, username=user.username, password=password)
            if authenticated_user:
                login(request, authenticated_user)

            messages.success(request, 'Password reset successful')
            return redirect('signin')
        else:
            messages.warning(request, 'Passwords do not match')
            return redirect("confirm_password")

        #     messages.success(request, 'Password reset successful')
        #     return redirect('signin')


        # else:
        #     messages.warning(request, 'Passwords do not match')
        #     print('not set')
        #     return redirect("confirm_password")
    return render(request,'login/confirm_password.html')

def profile_forget_password(request,user_id):
    user = User.objects.get(id=user_id)
    if request.user.id != user.id:
        return render(request, 'login/signin.html', {'error_message': 'Unauthorized access'})
    request.session['email'] = user.email
    request.session['verification_type'] = 'profile_forget_password'
    send_otp(request)
    return render(request,'login/verify_otp.html')

def profile_confrim_password(request):
    if request.method == "POST":
        password = request.POST.get('password1')
        confirm_password = request.POST.get('password2')

        print(password)
        if password == confirm_password:
            email = request.session.get('email')
            print(email)
            user = User.objects.get(email=email)
            print(user)
            user.set_password(password)  
            user.save()
            print('set')


            authenticated_user = authenticate(request, username=user.username, password=password)
            if authenticated_user:
                login(request, authenticated_user)

            messages.success(request, 'Password reset successful')
            return redirect('user_profile')
        else:
            messages.warning(request, 'Passwords do not match')
            return redirect("confirm_password")
    return render(request,'login/confirm_password.html')



def Logout(request):    
    request.session.flush()
    logout(request)
    return redirect('/')

