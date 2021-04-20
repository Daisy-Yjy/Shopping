from django.urls import path

from . import views


urlpatterns = [
    # 获取支付宝支付url
    path(r'<int:order_id>/', views.PaymentView.as_view()),
    # 支付后验证状态
    path(r'status/', views.PaymentStatusView.as_view()),
]