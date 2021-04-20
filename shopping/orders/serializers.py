from django.utils.datetime_safe import datetime
from rest_framework import serializers
from decimal import Decimal
from django_redis import get_redis_connection
from django.db import transaction

from goods.models import SKU
from .models import OrderInfo, OrderGoods


class CartSKUSerializer(serializers.ModelSerializer):
    """结算订单中的商品序列化器"""

    count = serializers.IntegerField(label='商品的购买数量')

    class Meta:
        model = SKU
        fields = ['id', 'name', 'default_image_url', 'price', 'count']


class OrderSettlementSerializer(serializers.Serializer):
    """结算订单序列化器"""

    skus = CartSKUSerializer(many=True)
    freight = serializers.DecimalField(label='运费', max_digits=10, decimal_places=2)


class SaveOrderSerializer(serializers.ModelSerializer):
    """保存订单序列化"""

    class Meta:
        model = OrderInfo
        fields = ['address', 'pay_method', 'order_id']
        read_only_fields = ['order_id']
        extra_kwargs = {
            'address': {'write_only': True, 'required': True},
            'pay_method': {'write_only': True, 'required': True},
        }

    def create(self, validated_data):  # 同时操作四张表 OrderInfo/sku/spu/OrderGoods
        user = self.context['request'].user
        # 生成订单编号
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + '%09d' % user.id
        address = validated_data.get('address')
        pay_method = validated_data.get('pay_method')
        status = OrderInfo.ORDER_STATUS_ENUM['UNPAID']

        with transaction.atomic():  # 手动开启事务
            save_point = transaction.savepoint()
            try:
                # 保存订单基本信息OrderInfo
                orderInfo = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,  # 订单中商品总数量
                    total_amount=Decimal('0.00'),  # 订单总金额
                    freight=Decimal('10.00'),
                    pay_method=pay_method,
                    status=status
                )
                redis_conn = get_redis_connection('cart')
                cart_dict_redis = redis_conn.hgetall('cart_%d' % user.id)
                selected_ids = redis_conn.smembers('selected_%d' % user.id)

                for sku_id_bytes in selected_ids:
                    while True:  # 让用户对同一个商品有无限次下单机会,只到库存真的不足为止
                        sku = SKU.objects.get(id=sku_id_bytes)
                        buy_count = int(cart_dict_redis[sku_id_bytes])
                        origin_sales = sku.sales
                        origin_stock = sku.stock
                        if buy_count > origin_stock:
                            raise serializers.ValidationError('库存不足')
                        new_sales = origin_sales + buy_count
                        new_stock = origin_stock - buy_count
                        # .update更新时会返回更新数据条数
                        result = SKU.objects.filter(stock=origin_stock, id=sku_id_bytes).update(stock=new_stock,
                                                                                                sales=new_sales)
                        if result == 0:  # 如果没有修改成功,说明有抢夺
                            continue

                        # 保存 修改spu销量
                        spu = sku.goods
                        spu.sales = spu.sales + buy_count
                        spu.save()

                        # 保存订单商品信息 OrderGoods
                        OrderGoods.objects.create(
                            order=orderInfo,
                            sku=sku,
                            count=buy_count,
                            price=sku.price,
                        )
                        orderInfo.total_count += buy_count
                        orderInfo.total_amount += (sku.price * buy_count)
                        break  # 当前这个商品下单成功,跳出死循环,进行对下一个商品下单
                orderInfo.total_amount += orderInfo.freight
                orderInfo.save()
            except Exception:
                # 回滚
                transaction.savepoint_rollback(save_point)
                raise serializers.ValidationError('库存不足')
            else:
                transaction.savepoint_commit(save_point)

        # 清除redis中已结算的商品)
        redis_conn.hdel('cart_%d' % user.id, *selected_ids)
        redis_conn.srem('selected_%d' % user.id, *selected_ids)
        return orderInfo


class UserOrderSerializer(serializers.ModelSerializer):
    """用户订单"""

    skus = serializers.StringRelatedField(many=True)

    class Meta:
        model = OrderInfo
        fields = ['create_time', 'order_id', 'total_amount', 'pay_method', 'status', 'skus']
