from django.contrib import admin

from .models import GoodsCategory, GoodsChannel, Brand, Goods, GoodsSpecification, SpecificationOption, SKU, SKUImage, \
    SKUSpecification, ContentCategory, Content

admin.site.register(GoodsCategory)
admin.site.register(GoodsChannel)
admin.site.register(Brand)
admin.site.register(Goods)
admin.site.register(GoodsSpecification)
admin.site.register(SpecificationOption)
admin.site.register(SKU)
admin.site.register(SKUImage)
admin.site.register(SKUSpecification)
admin.site.register(ContentCategory)
admin.site.register(Content)
