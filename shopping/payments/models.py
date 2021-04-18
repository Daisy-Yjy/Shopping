from django.db import models

from orders.models import OrderInfo


class Payment(models.Model):
    """支付信息"""
    order = models.ForeignKey(OrderInfo, on_delete=models.CASCADE, verbose_name='订单')
    trade_id = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name='支付编号')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = 'tb_payment'
        verbose_name = '支付信息'
        verbose_name_plural = verbose_name
