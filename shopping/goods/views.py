from django_redis import get_redis_connection
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListAPIView, CreateAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SKU
from .serializers import SKUSerializer, SKUDetailSerializer, UserBrowserHistorySerializer


class SKUListView(ListAPIView):
    """商品列表数据查询"""

    filter_backends = [OrderingFilter, SearchFilter]
    ordering_fields = ['create_time', 'price', 'sales']
    search_fields = ['name']

    serializer_class = SKUSerializer

    def get_queryset(self):
        """重写queryset"""

        category_id = self.kwargs.get('category_id')
        return SKU.objects.filter(is_launched=True, category_id=category_id)


class SKUDetailView(APIView):
    """单一商品详情"""

    def get(self, request, sku_id):

        queryset = SKU.objects.get(is_launched=True, id=sku_id)
        serializer = SKUDetailSerializer(queryset)

        return Response(serializer.data)


class UserBrowserHistoryView(CreateAPIView, GenericAPIView):
    """商品浏览记录"""
    serializer_class = UserBrowserHistorySerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        redis_conn = get_redis_connection('history')
        user = request.user
        # 获取redis中当前用户的浏览记录列表数据
        sku_ids = redis_conn.lrange('history_%d' % user.id, 0, -1)
        # sku模型中sku_id顺序查询
        sku_list = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            sku_list.append(sku)
        serializer = SKUSerializer(sku_list, many=True)
        return Response(serializer.data)