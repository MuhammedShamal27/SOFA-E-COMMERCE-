from datetime import timezone
from django.db import models
from django.contrib.auth.models import User 


class Banner(models.Model):
    banner_img = models.ImageField(upload_to='media/banner/image', null=True, blank=True)
    subtitle = models.CharField(max_length=50, blank=True, null=True)  
    title = models.CharField(max_length=50, blank=True, null=True)  

class Coupons(models.Model):
    coupon_code = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    minimum_amount = models.IntegerField(default=10000)
    discount = models.IntegerField(default=0)
    is_expired = models.BooleanField(default=False)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    un_list= models.BooleanField(default=False)

    def __str__(self):
        return self.coupon_code

    def is_valid(self):
        now = timezone.now()
        return now >= self.valid_from and now <= self.valid_to


    def is_used_by_user(self, user):
        redeemed_details = UserCoupons.objects.filter(coupon=self, user=user, is_used=True)
        return redeemed_details.exists()


class UserCoupons(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    coupon = models.ForeignKey(Coupons, on_delete=models.CASCADE)
    is_used = models.BooleanField(default=True)

    def __str__(self):
        return self.coupon.coupon_code