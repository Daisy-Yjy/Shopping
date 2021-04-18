from django.urls import path

from . import views


urlpatterns = [
    # 购物车增删改查
    path(r'carts/', views.CartView.as_view()),
    # 购物车全选
    path(r'carts/selection/', views.CartSelectedAllView.as_view()),
]