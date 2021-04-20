import os
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from alipay import AliPay

from orders.models import OrderInfo
from shopping import settings

from .models import Payment


class PaymentView(APIView):
    """生成支付链接"""

    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        user = request.user
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return Response({'message': '订单有误'}, status=status.HTTP_400_BAD_REQUEST)
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_string=open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys/app_private_key.pem')).read(),
            # 指定应用自己的私钥文件绝对路径
            alipay_public_key_string=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                'keys/alipay_public_key.pem')).read(),
            sign_type="RSA2",  # RSA 或者 RSA2  加密方式推荐使用RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )
        # 拼接支付链接
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 马上要支付的订单编号
            total_amount=str(order.total_amount),  # 支付总金额, 不能为Decimal
            subject='Shopping%s' % order_id,  # 标题
            return_url="http://127.0.0.1:8000/payments/status/",  # 支付成功后的回调url
        )
        alipay_url = settings.ALIPAY_URL + '?' + order_string
        return Response({'alipay_url': alipay_url})


class PaymentStatusView(APIView):
    """修改订单状态,保存支付宝交易号"""

    def put(self, request):
        queryDict = request.query_params
        data = queryDict.dict()
        sign = data.pop('sign')
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_string=open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys/app_private_key.pem')).read(),  # 指定应用自己的私钥文件绝对路径
            alipay_public_key_string=open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys/alipay_public_key.pem')).read(),  # 指定支付宝公钥文件的绝对路径
            sign_type="RSA2",  # RSA 或者 RSA2  加密方式推荐使用RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )

        # 调用alipay SDK的verify方法进行验证支付结果
        success = alipay.verify(data, sign)
        if success:
            order_id = data.get('out_trade_no')
            trade_no = data.get('trade_no')
            Payment.objects.create(
                order_id=order_id,
                trade_id=trade_no
            )
            # 修改订单状态
            OrderInfo.objects.filter(order_id=order_id, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']).update(
                status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'])
            return Response({'trade_id': trade_no})
        return Response({'message': '非法请求'}, status=status.HTTP_403_FORBIDDEN)