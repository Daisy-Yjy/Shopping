from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """用户模型类"""

    mobile = models.CharField(max_length=11, unique=True, verbose_name='手机号')
    default_address = models.ForeignKey('Address', related_name='users', null=True, blank=True,
                                        on_delete=models.SET_NULL, verbose_name='默认地址')

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username


class Area(models.Model):
    """省市区模型"""

    name = models.CharField(max_length=20, verbose_name='名称')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='subs', null=True, blank=True,
                               verbose_name='省市区')

    class Meta:
        db_table = 'tb_areas'
        verbose_name = '省市区'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Address(models.Model):
    """用户地址"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name='用户')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    province = models.ForeignKey(Area, on_delete=models.PROTECT, related_name='province_addresses',
                                 verbose_name='省')
    city = models.ForeignKey(Area, on_delete=models.PROTECT, related_name='city_addresses', verbose_name='市')
    district = models.ForeignKey(Area, on_delete=models.PROTECT, related_name='district_addresses',
                                 verbose_name='区')
    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_address'
        verbose_name = '用户地址'
        verbose_name_plural = verbose_name
        ordering = ['-update_time']

    def __str__(self):
        return self.receiver
