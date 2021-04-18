import base64
import pickle

from django_redis import get_redis_connection


def merge_cart_cookie_to_redis(request, user, response):
    """
    登录时合并购物车
    :param request: 请求对象
    :param user: 用户对象
    :param response: 响应对象
    :return:
    """

    cart_str = request.COOKIES.get('cart')

    if cart_str is None:  # 没有cookie购物车数据,直接返回
        return
    cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
    redis_conn = get_redis_connection('cart')

    # cookie数据存储到redis中
    for sku_id in cart_dict:
        redis_conn.hset('cart_%d' % user.id, sku_id, cart_dict[sku_id]['count'])
        if cart_dict[sku_id]['selected']:
            redis_conn.sadd('selected_%d' % user.id, sku_id)
    # 删除cookie购物车数据
    response.delete_cookie('cart')