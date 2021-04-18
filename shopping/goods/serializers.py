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