from django.db import models

"""
用户表
@ username: 用户名
@ password: 密码
@ email: 邮箱
@ permission: 权限，0为普通用户，1为养殖户，2为管理员
"""


class User(models.Model):
    username = models.CharField(max_length=20)
    password = models.CharField(max_length=20)
    email = models.EmailField()
    permission = models.IntegerField(default=0)


"""
@ Year：年
@ Date：年月日
@ Latin_Name：鱼群名
@ Count：统计数量
@ Mean_Length：平均长度
@ Mean_Weight：平均重量
"""


class FishInfo(models.Model):
    year = models.IntegerField()
    date = models.DateField()
    latin_name = models.CharField(max_length=30)
    count = models.IntegerField()
    mean_length = models.FloatField()
    mean_weight = models.FloatField()


"""
@ Date:日期
@ temp:温度
@ pH:pH值
@ Ox:含氧量
@ Dao:导电率
@ Zhuodu:浊度
@ Yandu:盐度
@ Andan:氨氮
@ Zonglin:总磷
@ Zongdan:总氮
"""


class WaterInfo(models.Model):
    Date = models.IntegerField()
    temp = models.FloatField()
    pH = models.FloatField()
    Ox = models.FloatField()
    Dao = models.FloatField()
    Zhuodu = models.FloatField()
    Yandu = models.FloatField()
    Andan = models.FloatField()
    Zonglin = models.FloatField()
    Zongdan = models.FloatField()


"""
@ Province:省名
@ Class:水质等级
@ temp:温度
@ pH:pH值
@ Ox:含氧量
@ Dao:导电率
@ Zhuodu:浊度
@ Yandu:盐度
@ Andan:氨氮
@ Zonglin:总磷
@ Zongdan:总氮
"""


class MapWaterInfo(models.Model):
    Province = models.CharField(max_length=30)
    Class = models.IntegerField()
    temp = models.FloatField()
    pH = models.FloatField()
    Ox = models.FloatField()
    Dao = models.FloatField()
    Zhuodu = models.FloatField()
    Yandu = models.FloatField()
    Andan = models.FloatField()
    Zonglin = models.FloatField()
    Zongdan = models.FloatField()


class FishBaike(models.Model):
    """
    @ name: 鱼名
    @ alias: 别名
    @ distribution: 分布
    @ food: 食物
    @ appearance: 外貌
    @ brief_intro: 简介
    """

    name = models.CharField(max_length=32)
    alias = models.CharField(max_length=128)
    distribution = models.CharField(max_length=256)
    food = models.CharField(max_length=256)
    appearance = models.TextField(max_length=1024)
    brief_intro = models.TextField(max_length=2048)
