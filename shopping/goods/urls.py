from django.urls import re_path, path

from . import views

urlpatterns = [
    # 商品列表数据
    path(r'categories/<int:category_id>/skus/', views.SKUListView.as_view()),
    # 单一商品详情
    path(r'sku/<int:sku_id>/', views.SKUDetailView.as_view()),
    # 商品浏览记录
    path(r'browse_histories/', views.UserBrowserHistoryView.as_view()),
]