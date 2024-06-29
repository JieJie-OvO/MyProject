"""
URL configuration for GroupWork project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# 修改2

# 第二次修改
from django.contrib import admin
from django.urls import path
from neo.views import *

from neo import views

urlpatterns = [
    path("system/welcome.html", welcome),
    # from this
    path("admin/", admin.site.urls),
    path("system/", system),
    path("system/index/", Index),
    path("system/MainInfo.html", views.MainInfo),
    path("system/Underwater.html", views.Underwater),
    path("system/datacenter.html", views.Datacenter),
    path("system/AIcenter.html", views.AIcenter),
    path("system/admincontrol.html", views.AdminControl),
    path("system/forget.html", views.forget),
    path("system/smart_QA.html", views.smart_qa),
    path("system/map.html", views.map),
    # 注册登录
    path("", login),
    path("system/register.html", register_page, name="register"),
    path("system/", system),
    path("backend/backend.html", backend),
    path("backend/table.html", table),
    path("backend/get_data", get_data),
    path("backend/edit_data", edit_data),
    path("backend/edit_check", edit_check),
    # 鱼群
    path("fish/get_fish_statistics", get_fish_statistics),
    path("fish/getTOP5", getTOP5),
    path("fish/get_fish_change", get_fish_change),
    path("fish/get_top_info", get_top_info),
    path("fish/writeDB", writ1eDB),
    path("fish/predict", fish_predict),
    # 水质
    path("water/get_water_statistics", get_water_statistics),
    path("water/writeDB", writ2eDB),
    path("water/get_water_info", get_water_info),
    path("water/map/writeDB", writ3eDB),
    path("water/predict", water_predict),
    path("water/water_export", water_exportdata),
    path("water/add", water_add),
    path('water/get_map_info',get_map_info),
    

    # 视频+图像
    path("pic/upload_video", views.upload_video),
    path("pic/switch_video", views.switch_video),
    path("pic/analysis_video", views.analysis_video),
    # 鱼类百科
    path("fishbaike/download", download_fish_baike),
    path("fishbaike/add", fishbaike_add),
    path("fishbaike/remove", fishbaike_remove),
    path("fishbaike/modify", fishbaike_modify),
    path("fishbaike/writeDB", writeDB_fishbaike),
    path("fishbaike/export", fishbaike_exportdata),
    path("fishbaike/search", fishbaike_search),
    path("fishbaike/showdetail", fishbaike_showdetail),
    # 天气
    path("weather/weekreport", weather_weekreport),
    path("weather/changeloc", weather_changeloc),
    path("weather/fresh", weather_fresh),
    path("404", case404),

    path("backend/MainInfo.html", views.MainInfo),
    path("backend/Underwater.html", views.Underwater),
    path("backend/datacenter.html", views.Datacenter),
    path("backend/AIcenter.html", views.AIcenter),
    path("backend/admincontrol.html", views.AdminControl),
    path("backend/forget.html", views.forget),
    path("backend/smart_QA.html", views.smart_qa),
    path("backend/map.html", views.map),
    path("backend/role.html", role_info),
    path("backend/project.html", project_info),

    # smartQA
    path("smartQA/ask", views.smartQA),
]
