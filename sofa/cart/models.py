from django.db import models
from django.contrib.auth.models import User
from home.models import *

# Create your models here.
class Cart(models.Model):
    cart_id=models.CharField(max_length=50, blank=True)
    user=models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    added_date=models.DateField(auto_now_add=True)

    def __str__(self):
        return self.cart_id
    
class Cartitem(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,null=True)
    product=models.ForeignKey(Products,on_delete=models.CASCADE,null=True)
    cart=models.ForeignKey(Cart,on_delete=models.CASCADE,null=True)
    quantity=models.IntegerField()
    is_active=models.BooleanField(default=True)

    def sub_total(self):
        return self.product.offer_price * self.quantity
    
    def __str__(self):
        return self.product.product_name
    

    
class Order(models.Model):
    STATUS = [
        ('New', 'New'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Returned', 'Returned'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    order_number = models.CharField(max_length=200)
    address=models.ForeignKey(Address,on_delete=models.SET_NULL,blank=True,null=True)
    order_total = models.FloatField()
    status = models.CharField(max_length=100, choices=STATUS, default='New')
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    discount = models.FloatField(default=0)


    def __str__(self):
        if self.user:
            return f"Order {self.order_number} for {self.user.username}"
        else:
            return f"Order {self.order_number} (No user assigned)"


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=100,default='Cancelled')
    amount_paid = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    discount = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.payment_method

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    product_price = models.FloatField()
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.product.product_name