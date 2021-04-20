import random
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, RetrieveAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.views import ObtainJSONWebToken
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from .models import User, Address, Area
from .serializers import CreateUserSerializer, UserAddressSerializer, UserDetailSerializer, SubsSerializer, \
    AreaSerializer
from libs.yuntongxun import sms

from carts.utils import merge_cart_cookie_to_redis


class UsernameCountView(APIView):
    """判断用户是否已注册"""

    def get(self, request, username):

        count = User.objects.filter(username=username).count()
        data = {'username': username, 'count': count}
        return Response(data)


class MobileCountView(APIView):
    """判断手机号是否已注册"""

    def get(self, request, mobile):

        count = User.objects.filter(mobile=mobile).count()

        data = {'mobile': mobile, 'count': count}
        return Response(data)


class SMSCodeView(APIView):
    """短信验证码"""

    def get(self, request, mobile):
        redis_conn = get_redis_connection('sms_codes')
        send_flag = redis_conn.get('sms_%s' % mobile)
        if send_flag:
            return Response({'message': '短信验证码发送频繁'}, status=status.HTTP_400_BAD_REQUEST)
        sms_codes = '%06d' % random.randint(0, 999999)
        # 发送验证码
        sms.CCP().send_template_sms(mobile, [sms_codes, 5], 1)

        redis_conn.setex('sms_%s' % mobile, 300, sms_codes)
        redis_conn.setex('send_flag_%s' % mobile, 60, sms_codes)

        return Response({'message': 'OK'})


class UserCreateView(CreateAPIView):
    """用户注册"""

    serializer_class = CreateUserSerializer


def jwt_response_payload_handler(token, user=None, request=None):
    """
    自定义jwt认证成功返回数据
    """
    return {
        'token': token,
        'user_id': user.id,
        'username': user.username
    }


class UserLoginView(ObtainJSONWebToken):
    """自定义账号密码登录"""

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.object.get('user') or request.user
            token = serializer.object.get('token')
            response_data = jwt_response_payload_handler(token, user, request)
            response = Response(response_data)
            # 账号登录时合并购物车
            merge_cart_cookie_to_redis(request, user, response)
            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginMobileView(APIView):
    """手机号验证码登录"""

    def post(self, request, *args, **kwargs):
        mobile = request.mobile
        sms_code = request.sms_code
        user = request.user
        redis_conn_sms = get_redis_connection('sms_codes')
        real_sms_code = redis_conn_sms.get('sms_%s' % mobile)
        if real_sms_code is None or sms_code != real_sms_code.decode():
            return Response({'message': '短信验证码错误'})

        # 生成token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER  # 引用jwt_payload_handler函数(生成payload)
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER  # 生成jwt
        payload = jwt_payload_handler(user)  # 根据user生成用户相关的载荷
        token = jwt_encode_handler(payload)  # 传入载荷生成完整的jwt
        user.token = token
        response_data = {'user_id': user.id, 'username': user.username, 'token': token}
        response = Response(response_data)
        # 账号登录时合并购物车
        merge_cart_cookie_to_redis(request, user, response)
        return response


class UserDetailView(RetrieveAPIView):
    """用户详细信息展示"""

    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class AddressViewSet(CreateModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    """用户收货地址增删改"""

    permission_classes = [IsAuthenticated]
    serializer_class = UserAddressSerializer

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    def create(self, request, *args, **kwargs):
        user = request.user
        count = Address.objects.filter(user=user).count()
        if count >= 20:
            return Response({'message': '收货地址数量上限'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        queryset = request.user.addresses.filter(is_deleted=False)
        serializer = self.get_serializer(queryset, many=True)
        user = request.user
        return Response({'user_id': user.id, 'default_address_id': user.default_address_id, 'limit': 20, 'addresses': serializer.data})

    def destroy(self, request, *args, **kwargs):
        address = self.get_object()
        # 逻辑删除
        address.is_deleted = True
        address.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['put'], detail=True)
    def status(self, request, pk=None):
        """设置默认地址"""
        address = Address.objects.get(id=pk)
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)


class AreaListView(ListAPIView):
    """查询所有省"""

    serializer_class = AreaSerializer
    queryset = Area.objects.filter(parent=None)

    def get(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AreaDetailView(RetrieveAPIView):
    """查单一省市"""

    def get(self, request, pk):
        try:
            area = Area.objects.get(id=pk)
        except Area.DoesNotExist:
            return Response({'message': '无效pk'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = SubsSerializer(area)
        return Response(serializer.data)

