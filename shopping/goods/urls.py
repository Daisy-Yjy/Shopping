from django.urls import re_path

from . import views

urlpatterns = [
    # 商品列表数据
    re_path(r'^categories/(?P<category_id>\d+)/skus/', views.SKUListView.as_view()),
    # 单一商品详情
    re_path(r'^sku/(?P<sku_id>\d+)/', views.SKUDetailView.as_view()),
]