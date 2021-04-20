import base64
import pickle
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CartSerializer, SKUCartSerializer, CartDeletedSerializer, CartSelectedAllSerializer
from goods.models import SKU


class CartView(APIView):
    """购物车增删改查"""

    def perform_authentication(self, request):
        """重写此方法,直接pass,可延后认证"""
        pass

    def post(self, request):
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')
        try:
            user = request.user
        except:
            user = None
        if user and user.is_authenticated:  # 登录用户redis数据存储
            redis_conn = get_redis_connection('cart')
            redis_conn.hincrby('cart_%d' % user.id, sku_id, count)
            if selected:
                redis_conn.sadd('selected_%d' % user.id, sku_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:  # 未登录用户cookie数据存储
            cart_str = request.COOKIES.get('cart')
            if cart_str:  # 字符串转为字典
                cart_str_bytes = cart_str.encode()
                cart_bytes = base64.b64decode(cart_str_bytes)
                cart_dict = pickle.loads(cart_bytes)
            else:
                cart_dict = {}

            if sku_id in cart_dict:
                origin_count = cart_dict[sku_id]['count']
                count += origin_count

            cart_dict[sku_id] = {'count': count, 'selected': selected}
            # 字典转为字符串储存
            cart_bytes = pickle.dumps(cart_dict)
            cart_str_bytes = base64.b64encode(cart_bytes)
            cart_str = cart_str_bytes.decode()
            response = Response(serializer.data, status=status.HTTP_201_CREATED)
            # 设置cookie
            response.set_cookie('cart', cart_str)
        return response

    def get(self, request):
        try:
            user = request.user
        except:
            user = None

        if user and user.is_authenticated:  # 登录用户
            redis_conn = get_redis_connection('cart')
            cart_redis_dict = redis_conn.hgetall('cart_%d' % user.id)
            selecteds = redis_conn.smembers('selected_%d' % user.id)

            # 将redis购物车数据格式转换成和cookie购物车数据格式一致
            cart_dict = {}
            for sku_id_bytes, count_bytes in cart_redis_dict.items():
                cart_dict[int(sku_id_bytes)] = {
                    'count': int(count_bytes),
                    'selected': sku_id_bytes in selecteds
                }
        else:  # 未登录用户
            cart_str = request.COOKIES.get('cart')
            if cart_str:
                cart_str_bytes = cart_str.encode()
                cart_bytes = base64.b64decode(cart_str_bytes)
                cart_dict = pickle.loads(cart_bytes)
            else:
                return Response({'message': '没有购物车数据'}, status=status.HTTP_400_BAD_REQUEST)
        sku_ids = cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)

        # 给每个对象多定义一个count和selected属性
        for sku in skus:
            sku.count = cart_dict[sku.id]['count']
            sku.selected = cart_dict[sku.id]['selected']
        serializer = SKUCartSerializer(skus, many=True)
        return Response(serializer.data)

    def put(self, request):
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')
        try:
            user = request.user
        except:
            user = None

        if user and user.is_authenticated:  # 登录用户
            redis_conn = get_redis_connection('cart')
            redis_conn.hset('cart_%d' % user.id, sku_id, count)
            if selected:
                redis_conn.sadd('selected_%d' % user.id, sku_id)
            else:
                redis_conn.srem('selected_%d' % user.id, sku_id)
            response = Response(serializer.data)
        else:  # 未登录用户
            cart_str = request.COOKIES.get('cart')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                return Response({'message': '没有获取到cookie'}, status=status.HTTP_400_BAD_REQUEST)

            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
            response = Response(serializer.data)
            response.set_cookie('cart', cart_str)
        return response

    def delete(self, request):
        serializer = CartDeletedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 获取校验后的数据 sku_id
        sku_id = serializer.validated_data.get('sku_id')
        try:
            user = request.user
        except:
            user = None

        # 构建响应对象
        response = Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
        if user and user.is_authenticated:  # 登录用户
            redis_conn = get_redis_connection('cart')
            redis_conn.hdel('cart_%d' % user.id, sku_id)
            redis_conn.srem('selected_%d' % user.id, sku_id)
        else:  # 未登录用户
            cart_str = request.COOKIES.get('cart')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                return Response({'message': 'cookie没有获取到'}, status=status.HTTP_400_BAD_REQUEST)
            if sku_id in cart_dict:
                del cart_dict[sku_id]

            if len(cart_dict.keys()):  # 如果cookie字典中还有商品, 把cookie字典转换成cookie
                cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
                response.set_cookie('cart', cart_str)
            else:  # 购物车数据已清空, 删除购物车cookie
                response.delete_cookie('cart')
        return response


class CartSelectedAllView(APIView):
    """购物车全选"""

    def perform_authentication(self, request):
        """重写此方法延后认证"""
        pass

    def put(self, request):
        serializer = CartSelectedAllSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        selected = serializer.validated_data.get('selected')
        try:
            user = request.user
        except:
            user = None

        if user and user.is_authenticated:  # 登录用户
            redis_conn = get_redis_connection('cart')
            cart_redis_dict = redis_conn.hgetall('cart_%d' % user.id)
            sku_ids = cart_redis_dict.keys()
            if selected:  # 把所有sku_id 添加到set集合
                redis_conn.sadd('selected_%d' % user.id, *sku_ids)
            else:  # 把所有sku_id 从set集合移除
                redis_conn.srem('selected_%d' % user.id, *sku_ids)
            response = Response(serializer.data)
        else:  # 未登录用户
            cart_str = request.COOKIES.get('cart')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                return Response({'message': 'cookie 没有获取到'}, status=status.HTTP_400_BAD_REQUEST)

            for sku_id in cart_dict:
                cart_dict[sku_id]['selected'] = selected
            cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
            response = Response(serializer.data)
            response.set_cookie('cart', cart_str)
        return response
