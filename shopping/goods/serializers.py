from django_redis import get_redis_connection
from rest_framework import serializers

from .models import SKU


class SKUSerializer(serializers.ModelSerializer):
    """sku商品序列化器"""

    class Meta:
        model = SKU
        fields = ['id', 'name', 'price', 'default_image_url', 'comments']


class SKUDetailSerializer(serializers.ModelSerializer):
    """sku单一商品序列化"""

    skuspecification_set = serializers.StringRelatedField(many=True)

    class Meta:
        model = SKU
        exclude = ['goods', 'category', 'cost_price', 'is_launched', 'create_time', 'update_time']


class UserBrowserHistorySerializer(serializers.Serializer):
    """商品浏览序列化器"""

    sku_id = serializers.IntegerField(label='商品sku_id', min_value=1)

    def validate_sku_id(self, value):
        """单独对sku_id进行校验"""
        try:
            SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('sku_id 不存在')
        return value

    def create(self, validated_data):
        sku_id = validated_data.get('sku_id')
        user = self.context['request'].user
        redis_conn = get_redis_connection('history')
        # 去重
        redis_conn.lrem('history_%d' % user.id, 0, sku_id)
        redis_conn.lpush('history_%d' % user.id, sku_id)
        redis_conn.ltrim('history_%d' % user.id, 0, 4)
        return validated_data