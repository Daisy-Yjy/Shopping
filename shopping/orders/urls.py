from django.urls import path

from . import views


urlpatterns = [
    # 去结算
    path(r'settlement/', views.OrderSettlementView.as_view()),
    # 保存订单
    path(r'', views.SaveOrderView.as_view()),
    # 查看订单
    path(r'user_orders/', views.UserOrderView.as_view()),
]