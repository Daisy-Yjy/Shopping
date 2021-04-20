from decimal import Decimal
from django_filters.rest_framework import DjangoFilterBackend
from django_redis import get_redis_connection
from rest_framework.filters import SearchFilter
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from goods.models import SKU
from .models import OrderInfo
from .serializers import OrderSettlementSerializer, SaveOrderSerializer, UserOrderSerializer


class OrderSettlementView(APIView):
    """去结算"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        redis_conn = get_redis_connection('cart')
        cart_dict_redis = redis_conn.hgetall('cart_%d' % user.id)
        selected_ids = redis_conn.smembers('selected_%d' % user.id)

        # 商品勾选状态和数量
        cart_dict = {}
        for sku_id_bytes in selected_ids:
            cart_dict[int(sku_id_bytes)] = int(cart_dict_redis[sku_id_bytes])
        sku_ids = cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        for sku in skus:  # 每个sku对象多定义一个count属性
            sku.count = cart_dict[sku.id]
        freight = Decimal('10.00')

        data_dict = {'freight': freight, 'skus': skus}
        serializer = OrderSettlementSerializer(data_dict)
        return Response(serializer.data)


class SaveOrderView(CreateAPIView):
    """保存订单"""

    serializer_class = SaveOrderSerializer
    permission_classes = [IsAuthenticated]


class UserOrderView(ListAPIView):
    """查看订单"""

    serializer_class = UserOrderSerializer
    # permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filter_fields = ['create_time', 'order_id', 'total_amount', 'pay_method', 'status']
    search_fields = ['create_time', 'order_id', 'total_amount', 'pay_method', 'status', 'skus']

    def get_queryset(self):
        # user = self.request.user
        # return OrderInfo.objects.filter(user=user)
        return OrderInfo.objects.filter(user_id=1)
