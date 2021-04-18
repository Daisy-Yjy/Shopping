from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SKU
from .serializers import SKUSerializer, SKUDetailSerializer


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
