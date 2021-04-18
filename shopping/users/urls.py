from django.urls import re_path, path

from . import views


urlpatterns = [
    # 判断用户名是否已注册
    re_path(r'usernames/(?P<username>\w{5,20})/count/', views.UsernameCountView.as_view()),
    # 判断手机号是否已注册
    re_path(r'mobiles/(?P<mobile>1[3-9]\d{9})/count/', views.MobileCountView.as_view()),
    # 发送短信验证码
    re_path(r'sms_codes/(?P<mobile>1[3-9]\d{9})/$', views.SMSCodeView.as_view()),
    # 注册用户
    path(r'users/', views.UserView.as_view()),
    # 账户 登录
    path(r'authorizations/', views.UserAuthorizeView.as_view()),
    # 手机号登录
    path('login/mobile/', views.LoginMobileView.as_view()),
    # 获取用户详情
    path(r'user/', views.UserDetailView.as_view()),
    # 地址 查列表, 新增
    path(r'addresses/', views.AddressViewSet.as_view({'get': 'list', 'post': 'create'})),
    path(r'addresses/<int:pk>/', views.AddressViewSet.as_view({'delete': 'destory', 'put': 'update'})),
    # 地址 修改 删除
    path(r'addresses/<int:pk>/status/', views.AddressViewSet.as_view({'put': 'status'})),
]