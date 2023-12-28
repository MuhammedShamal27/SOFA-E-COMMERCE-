from django.contrib import admin
from home.models import Products,Category
from .models import Banner,Coupons
# Register your models here.
admin.site.register(Products)
admin.site.register(Category)
admin.site.register(Banner)
admin.site.register(Coupons)

