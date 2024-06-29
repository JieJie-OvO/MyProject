from django.db.models import Avg
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, HttpRequest
from django.http import HttpResponseRedirect
from django.views.decorators.clickjacking import xframe_options_exempt
from GroupWork import settings
from model.smartQA.QARobot import SmartQARobot
from neo.models import User, FishInfo, WaterInfo, MapWaterInfo, FishBaike
from model.fish.LSTM_fish import LSTMModel,generate_wave_numbers
import re, json, os, time
import pandas as pd
import numpy as np
from time import sleep
from model.water.predict.predict import premanage, model_predict, water_predict_list
# import model.YOLO.detect as YOLO

from django.core.files.storage import FileSystemStorage
from tqdm import tqdm
import requests
from .spider.fish_spider import get_fish_infos
from .spider.weather_spider import get_city_infos, get_weather_infos
from datetime import datetime
from model.water.datatransfer import num2date, date2num

def smartQA(request):
    sqa = SmartQARobot()
    question = request.GET.get("q")
    answer = sqa.API(question)
    return JsonResponse({"answer": answer})

def case404(request):
    return render(request, "404.html")


# Create your views here.
def Index(request):

    return render(request, "index.html")


def welcome(request):
    return render(request, "welcome.html")


def forget(request):
    return render(request, "forget_code.html")


def system(request):

    uid = request.GET.get("uid")
    if uid == None:
        return redirect("/")
    user = User.objects.get(id=uid)
    dic = {0: "普通用户", 1: "批发商", 2: "养殖户", 3: "管理员", 4: "高级管理员"}

    with open("./information/per", "w", encoding="utf-8") as f:
        f.write(str(uid))

    return render(
        request,
        "system.html",
        {
            "uid": uid,
            "username": user.username,
            "permission": user.permission,
            "identity": dic[user.permission],
        },
    )

    # return render(request, 'system.html')


def MainInfo(request):
    res = get_water_statistics(request)
    data = json.loads(res.content)

    with open("./information/per", "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            uid = int(line)

    user = User.objects.get(id=uid)
    return render(
        request, "MainInfo.html", {"data": data, "permission": user.permission}
    )


def Underwater(request):
    res = get_fish_statistics(request)
    data = json.loads(res.content)
    print(data)
    return render(request, "Underwater.html", {"data": data})


def Datacenter(request):
    data = {
        "Prosess": 999,
        "disk_used": 1000,
        "disk_rest": 1500,
        "transport_time": "02:45",
        "CPU": 80,
        "memory": 60,
        "GPU": 50,
    }
    return render(request, "datacenter.html", data)


def AIcenter(request: HttpRequest):
    # ---天气---
    with open("./information/per", "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            uid = int(line)

    user = User.objects.get(id=uid)

    cur_province, cur_city, weather_days, weather_hours = (
        weather_get_cur_loc_weather_data()
    )
    cur_date = datetime.today().strftime("%m/%d")
    cur_hour = datetime.now().time().strftime("%H:%M")
    weather_day, weather_hour = {}, {}
    for i in range(len(weather_days)):
        if cur_date == weather_days[i]["date"]:
            weather_day = weather_days[i]
            les, mor = -1, -1
            for j in range(len(weather_hours[i])):
                if weather_hours[i][j]["hour"] <= cur_hour:
                    if (
                        les != -1
                        and weather_hours[i][les]["hour"] <= weather_hours[i][j]["hour"]
                    ):
                        les = j
                if weather_hours[i][j]["hour"] >= cur_hour:
                    if (
                        mor != -1
                        and weather_hours[i][mor]["hour"] >= weather_hours[i][j]["hour"]
                    ):
                        mor = j
            if mor != -1:
                weather_hour = weather_hours[i][mor]
            else:
                weather_hour = weather_hours[i][les]
            break
    # ---水质---
    water_preres = ""
    with open("./information/water_preres", "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            water_preres = int(line)
    water_res_list = []
    with open("./information/water_res", "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            water_res_list.append(int(line))
    water_res = {
        "温度": water_res_list[0],
        "PH": water_res_list[1],
        "溶氧量": water_res_list[2],
        "高猛酸盐": water_res_list[3],
        "氨氮": water_res_list[4],
        "总磷": water_res_list[5],
        "总氮": water_res_list[6],
    }

    if len(request.GET) == 0:
        return render(
            request,
            "AIcenter.html",
            {
                "water_preres": water_preres,
                "water_res": water_res,
                "water_predict_list": water_predict_list,
                "curloc": {"province": cur_province, "city": cur_city},
                "weather_day": weather_day,
                "weather_hour": weather_hour,
                "permission": user.permission,
            },
        )
    show = int(request.GET.get("show")[0])
    return render(
        request,
        "AIcenter.html",
        {
            "show": show,
            "water_preres": water_preres,
            "water_res": water_res,
            "curloc": {"province": cur_province, "city": cur_city},
            "weather_day": weather_day,
            "weather_hour": weather_hour,
            "permission": user.permission,
        },
    )


def AdminControl(request):
    return render(request, "admincontrol.html")


# 注册登录
def login(request):
    if request.method == "GET":
        # 先尝试从cookie登录
        usrname = request.COOKIES.get("username")
        pwd = request.COOKIES.get("password")
        try:
            user = User.objects.get(username=usrname)
            if (
                user.password == pwd and request.GET.get("status") != "quit"
            ):  # cookie验证成功，直接前往主页
                return redirect(f"/system/?uid={user.id}")
            # 否则渲染登录页
            return render(request, "login.html")
        except:
            return render(request, "login.html")
    # POST
    username = request.POST.get("username")
    password = request.POST.get("password")
    verify_code = request.POST.get("verify_code")  # 获取用户输入的验证码
    if str(verify_code).lower() != "xszg":
        return render(request, "login.html", {"error": "验证码错误！"})
    # 检查用户输入的用户名和密码
    curr_user = User.objects.filter(username=username)
    if len(curr_user) == 0:
        return render(request, "login.html", {"error": "用户名不存在！"})
    if curr_user[0].password != password:
        return render(request, "login.html", {"error": "密码错误！"})
    cookie = {"username": username, "password": password}
    response = HttpResponseRedirect("/system/")
    for k, v in cookie.items():
        response.set_cookie(k, v, max_age=60 * 60 * 24, path="/")  # 设置一天的cookie
    return response


def register_page(request):
    if request.method == "GET":
        return render(request, "register.html")
    # POST
    # 用户名不能重复
    username = request.POST.get("username")
    if len(User.objects.filter(username=username)) != 0:
        return render(request, "register.html", {"error": "用户名已存在！"})

    # 邮箱格式检查，并且邮箱不能重复
    email = request.POST.get("email")
    pattern = r"^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, str(email)):
        return render(request, "register.html", {"error": "邮箱格式错误！"})
    if len(User.objects.filter(email=email)) != 0:
        return render(request, "register.html", {"error": "邮箱已存在！"})

    password = request.POST.get("password")
    # 创建新用户
    User.objects.create(username=username, password=password, email=email)
    response = HttpResponseRedirect("/")  # 返回登录页
    # 创建新用户之后，删除所有cookie
    cookie_names = request.COOKIES.keys()
    for cookie_name in cookie_names:
        response.delete_cookie(cookie_name)
    return response


def edit_data(request):
    username = request.GET.get("username")
    return render(request, "edit.html", {"username": username})


def edit_check(request):
    username = request.POST.get("username")
    password = request.POST.get("password")
    email = request.POST.get("email")
    permission = request.POST.get("interest")

    # 定位原来的用户
    origin = request.POST.get("origin")
    user = User.objects.get(username=origin)
    user.username = username
    user.password = password
    user.email = email
    user.permission = permission
    user.save()
    return redirect("/backend/table.html")


def backend(request):
    return render(request, "backend.html")


def table(request):
    return render(request, "table.html")

def role_info(request):
    return render(request, "role.html")

def project_info(request):
    return render(request, "project.html")

def map(request):
    data = get_map_info(request)
    return render(request, "map.html", {"datas": data})


def get_data(request):
    users = list(User.objects.all().values())  # 获取所有用户数据，并转换为字典列表
    return JsonResponse({"code": 0, "data": users})


def smart_qa(request):
    return render(request, "smart_QA.html")


# 获取鱼类统计信息
def get_fish_statistics(request):
    # 获取当前绝对路径
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(BASE_DIR, "model/data/fish/processed")
    data = pd.read_csv(os.path.join(path, "fish.csv"), index_col=0)
    # 获取鱼类种类和数量
    fish_species = data["Latin_Name"].unique()
    fish_count = int(data["Count"].sum())
    data = pd.read_csv(os.path.join(path, "fish_final.csv"), index_col=0)
    # 获取平均体长和平均体重，保留两位小数
    mean_length = round(data["Mean_Length"].mean(), 2)
    mean_weight = round(data["Mean_Weight"].mean(), 2)
    return JsonResponse(
        {
            "fish_species": len(fish_species),
            "fish_count": fish_count,
            "mean_length": mean_length,
            "mean_weight": mean_weight,
        }
    )


def getTOP5(request):
    # 获取当前绝对路径
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(BASE_DIR, "model/data/fish/processed")
    data = pd.read_csv(os.path.join(path, "fish_cleaned.csv"), index_col=0)
    # 获取top5
    all_groups = data.groupby("Latin_Name")
    tuples = []
    for group_name in all_groups.groups:
        curr_group = all_groups.get_group(group_name)
        dates = curr_group["Date"].unique()
        tuples.append((group_name, len(dates)))
    tuples.sort(key=lambda x: x[1], reverse=True)
    tuples = tuples[:5]
    top5 = [{"value": tuples[i][1], "name": tuples[i][0]} for i in range(5)]
    return JsonResponse(top5, safe=False)


def get_fish_change(request):
    # 获取当前绝对路径
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(BASE_DIR, "model/data/fish/processed")
    data = pd.read_csv(os.path.join(path, "fish_time.csv"), index_col=0)
    data["Date"] = pd.to_datetime(data["Date"])
    return JsonResponse(data.to_dict(orient="list"))


def get_top_info(request):
    # 获取当前绝对路径
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(BASE_DIR, "model/data/fish/processed")
    with open(os.path.join(path, "top_info.json"), "r") as f:
        data = json.load(f)
    return JsonResponse(data, safe=False)


def writ1eDB(request):
    FishInfo.objects.all().delete()  # 防止重复写入
    usecols = ["Year", "Date", "Latin_Name", "Count", "Mean_Length", "Mean_Weight"]
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(BASE_DIR, "model/data/fish/processed")
    data = pd.read_csv(os.path.join(path, "fish_final.csv"), usecols=usecols)
    for i in range(len(data)):
        row = data.iloc[i]
        FishInfo.objects.create(
            year=row["Year"],
            date=row["Date"],
            latin_name=row["Latin_Name"],
            count=row["Count"],
            mean_length=row["Mean_Length"],
            mean_weight=row["Mean_Weight"],
        )
    return HttpResponse("success")


def fish_predict(request):
    if request.method == "GET":
        fish_species = FishInfo.objects.values("latin_name").distinct()
        return render(request, "fish_predict.html", {"fish_species": fish_species})
    else:
        fish_name = request.POST.get("fish_name")
        duration = int(request.POST.get("duration"))
        fish_data = FishInfo.objects.filter(latin_name=fish_name)
        # 当前的身长和体重
        curr_length = fish_data.aggregate(avg_length=Avg("mean_length"))["avg_length"]
        curr_weight = fish_data.aggregate(avg_weight=Avg("mean_weight"))["avg_weight"]

        data = pd.DataFrame(
            list(fish_data.values()),
            columns=[
                "id",
                "year",
                "date",
                "latin_name",
                "count",
                "mean_length",
                "mean_weight",
            ],
        )
        data["date_ordinal"] = data["date"].apply(lambda x: x.toordinal())
        data = data[["year", "date_ordinal", "count"]]
        data = np.array(data)[-1 * duration :]
        data = np.expand_dims(data, axis=0)

        # 获取当前绝对路径
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        SAVE_PATH = os.path.join(BASE_DIR, "model/data/fish/save")
        model = LSTMModel(3, 100, 2, 2, SAVE_PATH=SAVE_PATH)
        predictions = model.api(
            data,
            DATA_PATH=os.path.join(
                BASE_DIR, "model/data/fish/processed/fish_final.csv"
            ),
        )

        weights = generate_wave_numbers(curr_weight, predictions[1])
        lengths = generate_wave_numbers(curr_length, predictions[0])

        return render(request, "fish_predict.html", {"w": weights, "l": lengths})

        # return redirect(
        #     f"http://127.0.0.1:8000/system/AIcenter.html?show=1&w={predictions[1]}&l={predictions[0]}&ws={weights}&ls={lengths}"
        # )


# 获取水质统计信息
# '''
#     Date:日期
#     temp:温度
#     pH:pH值
#     Ox:含氧量
#     Dao:导电率
#     Zhuodu:浊度
#     Yandu:盐度
#     Andan:氨氮(暂不用)
#     Zonglin:总磷(暂不用)
#     Zongdan:总氮(暂不用)
# '''
def get_water_statistics(request):

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(BASE_DIR, "model/data/water/processed")
    data = pd.read_csv(os.path.join(path, "water_cleaned.csv"), index_col=0)
    all_items = WaterInfo.objects.order_by('id')
    all_items = all_items[::-1]

    if len(all_items) < 1000:
        # 获取统计图信息
        FormData = {}
        for tag in ["Day", "Week", "Month", "All"]:
            temp, pH, Ox, Dao, Zhuodu, Yandu = [], [], [], [], [], []

            step = 0

            if tag == "All":
                step = 300
            if tag == "Month":
                step = 140
            if tag == "Week":
                step = 70
            if tag == "Day":
                step = 30

            for i in range(7):
                temp.append(round(data["temp"].head((i + 1) * step).mean(), 3))
                pH.append(round(data["pH"].head((i + 1) * step).mean(), 3))
                Ox.append(round(data["Ox"].head((i + 1) * step).mean(), 3))
                Dao.append(round(data["Dao"].head((i + 1) * step).mean(), 3))
                Zhuodu.append(round(data["Zhuodu"].head((i + 1) * step).mean(), 3))
                Yandu.append(round(data["Yandu"].head((i + 1) * step).mean(), 3))

            if tag == "Day":
                Day = {
                    "temp": temp,
                    "pH": pH,
                    "Ox": Ox,
                    "Dao": Dao,
                    "Zhuodu": Zhuodu,
                    "Yandu": Yandu,
                }
                FormData[tag] = Day
            if tag == "Week":
                Week = {
                    "temp": temp,
                    "pH": pH,
                    "Ox": Ox,
                    "Dao": Dao,
                    "Zhuodu": Zhuodu,
                    "Yandu": Yandu,
                }
                FormData[tag] = Week
            if tag == "Month":
                Month = {
                    "temp": temp,
                    "pH": pH,
                    "Ox": Ox,
                    "Dao": Dao,
                    "Zhuodu": Zhuodu,
                    "Yandu": Yandu,
                }
                FormData[tag] = Month
            if tag == "All":
                All = {
                    "temp": temp,
                    "pH": pH,
                    "Ox": Ox,
                    "Dao": Dao,
                    "Zhuodu": Zhuodu,
                    "Yandu": Yandu,
                }
                FormData[tag] = All

        # 获取表格数据
        AvgData = {}
        for tag in ["temp", "pH", "Ox", "Dao", "Zhuodu", "Yandu"]:
            AvgData[tag] = round(data[tag].mean(), 3)
    
    else:
        # 获取统计图信息
        all_items
        FormData = {}
        for tag in ["Day", "Week", "Month", "All"]:
            temp, pH, Ox, Dao, Zhuodu, Yandu = [], [], [], [], [], []

            step = 0

            if tag == "All":
                step = 120
            if tag == "Month":
                step = 30
            if tag == "Week":
                step = 7
            if tag == "Day":
                step = 1

            for i in range(7):
                temp.append(all_items[i*step].temp)
                pH.append(all_items[i*step].pH)
                Ox.append(all_items[i*step].Ox)
                Dao.append(all_items[i*step].Dao)
                Zhuodu.append(all_items[i*step].Zhuodu)
                Yandu.append(all_items[i*step].Yandu)

            temp = temp[::-1]
            pH = pH[::-1]
            Ox = Ox[::-1]
            Dao = Dao[::-1]
            Zhuodu = Zhuodu[::-1]
            Yandu = Yandu[::-1]

            if tag == "Day":
                Day = {
                    "temp": temp,
                    "pH": pH,
                    "Ox": Ox,
                    "Dao": Dao,
                    "Zhuodu": Zhuodu,
                    "Yandu": Yandu,
                }
                FormData[tag] = Day
            if tag == "Week":
                Week = {
                    "temp": temp,
                    "pH": pH,
                    "Ox": Ox,
                    "Dao": Dao,
                    "Zhuodu": Zhuodu,
                    "Yandu": Yandu,
                }
                FormData[tag] = Week
            if tag == "Month":
                Month = {
                    "temp": temp,
                    "pH": pH,
                    "Ox": Ox,
                    "Dao": Dao,
                    "Zhuodu": Zhuodu,
                    "Yandu": Yandu,
                }
                FormData[tag] = Month
            if tag == "All":
                All = {
                    "temp": temp,
                    "pH": pH,
                    "Ox": Ox,
                    "Dao": Dao,
                    "Zhuodu": Zhuodu,
                    "Yandu": Yandu,
                }
                FormData[tag] = All

        # 获取表格数据
        AvgData = {}
        AvgData["temp"] = all_items[0].temp
        AvgData["pH"] = all_items[0].pH
        AvgData["Ox"] = all_items[0].Ox
        AvgData["Dao"] = all_items[0].Dao
        AvgData["Zhuodu"] = all_items[0].Zhuodu
        AvgData["Yandu"] = all_items[0].Yandu

    return JsonResponse({"FormData": FormData, "AvgData": AvgData})


def get_water_info(request):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(BASE_DIR, "model/data/water/processed")
    data = pd.read_csv(os.path.join(path, "water_cleaned.csv"), index_col=0)
    all_items = WaterInfo.objects.order_by('id')
    all_items = all_items[::-1]

    if len(all_items)<1000:
        # 获取统计图信息
        FormData = {}
        for tag in ["Day", "Week", "Month", "All"]:
            temp, pH, Ox, Dao, Zhuodu, Yandu = [], [], [], [], [], []

            step = 0

            if tag == "All":
                step = 300
            if tag == "Month":
                step = 140
            if tag == "Week":
                step = 70
            if tag == "Day":
                step = 30

            for i in range(7):
                temp.append(round(data["temp"].head((i + 1) * step).mean(), 3))
                pH.append(round(data["pH"].head((i + 1) * step).mean(), 3))
                Ox.append(round(data["Ox"].head((i + 1) * step).mean(), 3))
                Dao.append(round(data["Dao"].head((i + 1) * step).mean(), 3))
                Zhuodu.append(round(data["Zhuodu"].head((i + 1) * step).mean(), 3))
                Yandu.append(round(data["Yandu"].head((i + 1) * step).mean(), 3))

            if tag == "Day":
                Day = {
                    "temp": temp,
                    "pH": pH,
                    "Ox": Ox,
                    "Dao": Dao,
                    "Zhuodu": Zhuodu,
                    "Yandu": Yandu,
                }
                FormData[tag] = Day
            if tag == "Week":
                Week = {
                    "temp": temp,
                    "pH": pH,
                    "Ox": Ox,
                    "Dao": Dao,
                    "Zhuodu": Zhuodu,
                    "Yandu": Yandu,
                }
                FormData[tag] = Week
            if tag == "Month":
                Month = {
                    "temp": temp,
                    "pH": pH,
                    "Ox": Ox,
                    "Dao": Dao,
                    "Zhuodu": Zhuodu,
                    "Yandu": Yandu,
                }
                FormData[tag] = Month
            if tag == "All":
                All = {
                    "temp": temp,
                    "pH": pH,
                    "Ox": Ox,
                    "Dao": Dao,
                    "Zhuodu": Zhuodu,
                    "Yandu": Yandu,
                }
                FormData[tag] = All
    else:
        # 获取统计图信息
        all_items
        FormData = {}
        for tag in ["Day", "Week", "Month", "All"]:
            temp, pH, Ox, Dao, Zhuodu, Yandu = [], [], [], [], [], []

            step = 0

            if tag == "All":
                step = 120
            if tag == "Month":
                step = 30
            if tag == "Week":
                step = 7
            if tag == "Day":
                step = 1

            for i in range(7):
                temp.append(all_items[i*step].temp)
                pH.append(all_items[i*step].pH)
                Ox.append(all_items[i*step].Ox)
                Dao.append(all_items[i*step].Dao)
                Zhuodu.append(all_items[i*step].Zhuodu)
                Yandu.append(all_items[i*step].Yandu)

            temp = temp[::-1]
            pH = pH[::-1]
            Ox = Ox[::-1]
            Dao = Dao[::-1]
            Zhuodu = Zhuodu[::-1]
            Yandu = Yandu[::-1]

            if tag == "Day":
                Day = {
                    "temp": temp,
                    "pH": pH,
                    "Ox": Ox,
                    "Dao": Dao,
                    "Zhuodu": Zhuodu,
                    "Yandu": Yandu,
                }
                FormData[tag] = Day
            if tag == "Week":
                Week = {
                    "temp": temp,
                    "pH": pH,
                    "Ox": Ox,
                    "Dao": Dao,
                    "Zhuodu": Zhuodu,
                    "Yandu": Yandu,
                }
                FormData[tag] = Week
            if tag == "Month":
                Month = {
                    "temp": temp,
                    "pH": pH,
                    "Ox": Ox,
                    "Dao": Dao,
                    "Zhuodu": Zhuodu,
                    "Yandu": Yandu,
                }
                FormData[tag] = Month
            if tag == "All":
                All = {
                    "temp": temp,
                    "pH": pH,
                    "Ox": Ox,
                    "Dao": Dao,
                    "Zhuodu": Zhuodu,
                    "Yandu": Yandu,
                }
                FormData[tag] = All

    # 获取表格数据
    data = []
    data.append(FormData["Day"])
    data.append(FormData["Week"])
    data.append(FormData["Month"])
    data.append(FormData["All"])

    return JsonResponse(data, safe=False)


# 地图数据
def get_map_info(request):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(BASE_DIR, "model/data/water/processed/map")
    data = pd.read_csv(os.path.join(path, "全国.csv"), index_col=0)

    Province = data["Province"]
    Class = data["Class"]
    lists = [list(a) for a in zip(Province, Class)]
    keys = ["name", "value"]
    list_json = [dict(zip(keys, item)) for item in lists]
    str_json = json.dumps(list_json, indent=2, ensure_ascii=False)
    return str_json


def water_predict(request):
    if request.method == "GET":
        return render(request, "water_predict.html")
    else:
        water_data = []

        temp = request.POST.get("temperature1")
        temp = float(temp) if temp != "" else 10
        water_data.append(temp)

        PH = request.POST.get("PH1")
        PH = float(PH) if PH != "" else 7
        water_data.append(PH)

        Ox = request.POST.get("Ox1")
        Ox = float(Ox) if Ox != "" else 10
        water_data.append(Ox)

        water_data.append(0)
        water_data.append(0)

        gaomeng = request.POST.get("gaomeng1")
        gaomeng = float(gaomeng) if gaomeng != "" else 0.1
        water_data.append(gaomeng)

        andan = request.POST.get("andan1")
        andan = float(andan) if andan != "" else 0
        water_data.append(andan)

        zonglin = request.POST.get("zonglin1")
        zonglin = float(zonglin) if zonglin != "" else 0
        water_data.append(zonglin)

        zongdan = request.POST.get("zongdan1")
        zongdan = float(zongdan) if zongdan != "" else 0
        water_data.append(zongdan)

        water_error, count = premanage(water_data)
        res, water_predict = model_predict(water_error, count)

        with open("./information/water_preres", "w", encoding="utf-8") as f:
            f.write(water_predict)

        with open("./information/water_res", "w", encoding="utf-8") as f:
            for i in water_error:
                f.write(str(i) + "\n")

        return redirect("http://127.0.0.1:8000/system/AIcenter.html")


# 导入水质数据到数据库
def writ2eDB(request):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(BASE_DIR, "model/data/water/processed")
    data = pd.read_csv(os.path.join(path, "water_cleaned.csv"))

    WaterInfo.objects.all().delete()
    for i in range(len(data)):
        row = data.iloc[i]
        # print("--------------------")
        # print(row["Date"])
        # print(type(row["Date"]))
        WaterInfo.objects.create(
            Date=row["Date"],
            temp=row["temp"],
            pH=row["pH"],
            Ox=row["Ox"],
            Dao=row["Dao"],
            Zhuodu=row["Zhuodu"],
            Yandu=row["Yandu"],
            Andan=row["Andan"],
            Zonglin=row["Zonglin"],
            Zongdan=row["Zongdan"],
        )
    return HttpResponse("success")


def writ3eDB(request):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(BASE_DIR, "model/data/water/processed/map")
    data = pd.read_csv(os.path.join(path, "全国.csv"))

    MapWaterInfo.objects.all().delete()
    for i in range(len(data)):
        row = data.iloc[i]
        MapWaterInfo.objects.create(
            Province=row["Province"],
            Class=row["Class"],
            temp=row["temp"],
            pH=row["pH"],
            Ox=row["Ox"],
            Dao=row["Dao"],
            Zhuodu=row["Zhuodu"],
            Yandu=row["Yandu"],
            Andan=row["Andan"],
            Zonglin=row["Zonglin"],
            Zongdan=row["Zongdan"],
        )
    return HttpResponse("success")


def water_exportdata(request: HttpRequest):
    waterinfos = WaterInfo.objects.all()
    waterdata = {}
    count = 0
    for waterinfo in waterinfos:
        count += 1
        waterdata[count] = {
            "Date": num2date(waterinfo.Date),
            "temp": waterinfo.temp,
            "pH": waterinfo.pH,
            "Ox": waterinfo.Ox,
            "Dao": waterinfo.Dao,
            "Zhuodu": waterinfo.Zhuodu,
            "Yandu": waterinfo.Yandu,
            "Andan": waterinfo.Andan,
            "Zonglin": waterinfo.Zonglin,
            "Zongdan": waterinfo.Zongdan,
        }

    json_data = json.dumps(waterdata, indent=2, ensure_ascii=False)
    response = HttpResponse(json_data, content_type="application/json")
    response["Content-Disposition"] = 'attachment; filename="exportwater.json"'
    return response


def water_add(request):
    if request.method == "GET":
        return render(request, "water_add.html")
    else:

        water_data = []

        date_str = request.POST.get("date1")
        if date_str == "":
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")

        print("----------------------")
        print(date_str)

        temp = request.POST.get("temperature1")
        temp = float(temp) if temp != "" else 10
        water_data.append(temp)

        PH = request.POST.get("PH1")
        PH = float(PH) if PH != "" else 7
        water_data.append(PH)

        Ox = request.POST.get("Ox1")
        Ox = float(Ox) if Ox != "" else 10
        water_data.append(Ox)

        water_data.append(0)
        water_data.append(0)

        gaomeng = request.POST.get("gaomeng1")
        gaomeng = float(gaomeng) if gaomeng != "" else 0.1
        water_data.append(gaomeng)

        andan = request.POST.get("andan1")
        andan = float(andan) if andan != "" else 0
        water_data.append(andan)

        zonglin = request.POST.get("zonglin1")
        zonglin = float(zonglin) if zonglin != "" else 0
        water_data.append(zonglin)

        zongdan = request.POST.get("zongdan1")
        zongdan = float(zongdan) if zongdan != "" else 0
        water_data.append(zongdan)

        dao = request.POST.get("Dao1")
        dao = float(dao) if dao != "" else 500

        zhuodu = request.POST.get("Zhuodu1")
        zhuodu = float(zhuodu) if zhuodu != "" else 3.3

        water_error, count = premanage(water_data)
        res, water_predict = model_predict(water_error, count)

        with open("./information/water_preres", "w", encoding="utf-8") as f:
            f.write(water_predict)

        with open("./information/water_res", "w", encoding="utf-8") as f:
            for i in water_error:
                f.write(str(i) + "\n")

        WaterInfo.objects.create(
            Date=date2num(date_str),
            temp=temp,
            pH=PH,
            Ox=Ox,
            Dao=dao,
            Zhuodu=zhuodu,
            Yandu=gaomeng,
            Andan=andan,
            Zonglin=zonglin,
            Zongdan=zongdan,
        )

        return redirect("http://127.0.0.1:8000/system/MainInfo.html")


# 从这里开始是视频和图像处理：
def upload_video(request):
    if request.method == "POST" and request.FILES.get("video_file"):
        video_file = request.FILES["video_file"]
        upload_type = request.POST.get("upload_type", "unknown")

        # 构造保存路径
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        upload_dir = os.path.join(BASE_DIR, "neo\static\\video\\")
        print(upload_dir)
        video_file.name = f"{upload_type}.mp4"
        # 保存文件
        with open(os.path.join(upload_dir, video_file.name), "wb+") as destination:
            for chunk in video_file.chunks():
                destination.write(chunk)
        return render(request, "MainInfo.html")
    else:
        # 处理 GET 请求
        return render(request, "MainInfo.html", {"error": "未上传视频！"})


def switch_video(request):
    if request.method == "POST":
        upload_type = request.POST.get("upload_type", "unknown")

        # 构造路径
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        upload_dir = os.path.join(BASE_DIR, "neo\static\\video\\")
        upload_to_dir = os.path.join(BASE_DIR, "neo\static\\video\\test\\")
        src_name = f"{upload_type}.mp4"
        vid_name = f"test.mp4"

        # 从源目录复制到目标目录
        from shutil import copy2

        copy2(os.path.join(upload_dir, src_name), os.path.join(upload_to_dir, vid_name))

        return render(request, "AIcenter.html")
    else:
        # 处理 GET 请求
        return render(request, "AIcenter.html", {"error": "未选择视频！"})


def analysis_video(request):
    # type为鱼的英文名，可以根据字典映射到id
    type = YOLO.detect()
    # 打印来看已经可以正常输出Carcharodon_carcharias，但是返回不正常呢，大家测试的时候可以直接设置type等于巴拉巴拉来看看
    print(type)
    return render(request, "AIcenter.html", {"answer": {type}})


##############################################
# 鱼类百科
##############################################
def download_fish_baike(request):
    """爬取鱼百科信息并下载图片，耗时较长，慎用"""
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    baike_dir = os.path.join(BASE_DIR, "model/data/fish/baike")
    img_dir = os.path.join(baike_dir, "pics")
    if not os.path.exists(baike_dir):
        os.makedirs(baike_dir)
    fish_infos, fail_urls = get_fish_infos(baike_dir)
    hints: list[str] = []
    hints.append(
        "{} kinds of fish found and {} urls failed.".format(
            len(fish_infos), len(fail_urls)
        )
    )
    for fail_url in fail_urls:
        hints.append(fail_url)
    os.makedirs(img_dir, exist_ok=True)
    total_cnt, save_cnt = 0, 0
    for fish_name, fish_info in tqdm(fish_infos.items()):
        fish_img_urls = fish_info["images"]
        total_cnt += len(fish_img_urls)
        for idx, img_url in enumerate(fish_img_urls):
            img_name = f"{fish_name}_{idx:02d}.{img_url.split('.')[-1]}"
            img_path = os.path.join(img_dir, img_name)
            response = requests.get(img_url)
            if response.status_code == 200:
                with open(img_path, "wb") as fp:
                    fp.write(response.content)
                save_cnt += 1
            else:
                hints.append(f"{img_name}:{img_url} failed.")
            time.sleep(0.3)
    hints.append(f"{save_cnt:4d}/{total_cnt:4d} images saved.")
    return HttpResponse("\n".join(hints))


def writeDB_fishbaike(request):
    """
    导入鱼百科数据到数据库，数据文件在model/data/fish/baike下，文件名以fish_infos开头的json文件
    """
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    baike_dir = os.path.join(BASE_DIR, "model/data/fish/baike")
    data_paths: list[str] = []
    FishBaike.objects.all().delete()
    for file in os.listdir(baike_dir):
        file = os.path.basename(file)
        if file.endswith(".json") and file.startswith("fish_infos"):
            data_paths.append(os.path.join(baike_dir, file))
    for data_path in data_paths:
        with open(data_path, "r", encoding="utf-8") as rfp:
            data: dict[str:dict] = json.load(rfp)
            for name, info in data.items():
                FishBaike.objects.create(
                    name=name,
                    alias=info["alias"],
                    distribution=info["distribution"],
                    food=info["food"],
                    appearance="\n".join(info["appearance"]),
                    brief_intro="\n".join(info["brief-intro"]),
                )
    return HttpResponse("success")


def fishbaike_add(request: HttpRequest):
    if request.method == "GET":
        return render(request, "fishbaike_add.html")
    else:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        baike_dir = os.path.join(BASE_DIR, "model/data/fish/baike")
        # 更新json文件
        data_path = os.path.join(baike_dir, "fish_infos_add.json")
        name = request.POST.get("name")
        fishbaike_data = {
            "alias": request.POST.get("alias"),
            "distribution": request.POST.get("distribution"),
            "food": request.POST.get("food"),
            "appearance": request.POST.get("appearance"),
            "brief_intro": request.POST.get("brief_intro"),
        }
        all_fishbaike_data: dict[str:dict] = {}
        if os.path.isfile(data_path):
            with open(data_path, "r", encoding="utf-8") as rfp:
                all_fishbaike_data = json.load(rfp)
        all_fishbaike_data[name] = fishbaike_data
        with open(data_path, "w", encoding="utf-8") as wfp:
            json.dump(all_fishbaike_data, wfp, ensure_ascii=False, indent=2)
        # 保存图片
        img_dir = os.path.join(baike_dir, "pics")
        fs = FileSystemStorage(location=baike_dir)
        for i, img in enumerate(request.FILES.getlist("image_inputs")):
            img_path = os.path.join(
                img_dir,
                "{}_{:02d}.{}".format(name, i, img.name.split(".", maxsplit=1)[-1]),
            )
            fs.save(img_path, img)
        # 写入数据库
        FishBaike.objects.create(
            name=name,
            alias=fishbaike_data["alias"],
            distribution=fishbaike_data["distribution"],
            food=fishbaike_data["food"],
            appearance=fishbaike_data["appearance"],
            brief_intro=fishbaike_data["brief_intro"],
        )
        return redirect("http://127.0.0.1:8000/system/AIcenter.html")


def fishbaike_remove(request: HttpRequest):
    if request.method == "GET":
        name = request.GET.get("name")
        filter_result = FishBaike.objects.filter(name=name)
        if len(filter_result) == 0:
            return HttpResponse("未找到该鱼类({})的信息。".format(name))
        for fishinfo in filter_result:
            fishinfo.delete()
        return HttpResponse("成功删除所有({})的信息。".format(name))
    return HttpResponse("访问方式错误，请使用GET请求访问。")


def fishbaike_modify(request: HttpRequest):
    if request.method == "GET":
        name = request.GET.get("name")
        filter_result = FishBaike.objects.filter(name=name)
        if len(filter_result) == 0:
            return HttpResponse("未找到该鱼类({})的信息。".format(name))
        if len(filter_result) > 1:
            return HttpResponse(
                "数据库中存在多个名为{}的鱼类，请联系管理员解决。".format(name)
            )
        fishbaike = filter_result[0]
        return render(
            request,
            "fishbaike_modify.html",
            {
                "fishinfo": {
                    "name": fishbaike.name,
                    "alias": fishbaike.alias,
                    "distribution": fishbaike.distribution,
                    "food": fishbaike.food,
                    "appearance": fishbaike.appearance,
                    "brief_intro": fishbaike.brief_intro,
                }
            },
        )
    else:
        name = request.POST.get("name")
        filter_result = FishBaike.objects.filter(name=name)
        if len(filter_result) == 0:
            return HttpResponse("未找到该鱼类({})的信息。".format(name))
        if len(filter_result) > 1:
            return HttpResponse(
                "数据库中存在多个名为{}的鱼类，请联系管理员解决。".format(name)
            )
        print(request.POST.get("distribution"))
        fishbaike = filter_result[0]
        fishbaike.alias = request.POST.get("alias")
        fishbaike.distribution = request.POST.get("distribution")
        fishbaike.food = request.POST.get("food")
        fishbaike.appearance = request.POST.get("appearance")
        fishbaike.brief_intro = request.POST.get("brief_intro")
        fishbaike.save()
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        RELA_DIR = "model/data/fish/baike"
        baike_dir = os.path.join(BASE_DIR, RELA_DIR)
        all_pics = os.listdir(os.path.join(baike_dir, "pics"))
        images = [
            settings.STATIC_URL + "fish/baike/pics/" + pic
            for pic in all_pics
            if pic.startswith(name)
        ]
        return render(
            request,
            "fishbaike_detail.html",
            {
                "fish_info": {
                    "name": fishbaike.name,
                    "alias": fishbaike.alias,
                    "distribution": fishbaike.distribution,
                    "food": fishbaike.food,
                    "appearance": fishbaike.appearance.split("\n"),
                    "brief_intro": fishbaike.brief_intro.split("\n"),
                    "images": images,
                }
            },
        )


def fishbaike_search(request: HttpRequest):
    if request.method == "GET":
        name = request.GET.get("name")
        search_results: list[dict] = []
        for fishbaike in FishBaike.objects.all():
            if name in fishbaike.name or name in fishbaike.alias:
                search_results.append(
                    {"name": fishbaike.name, "alias": fishbaike.alias}
                )
        if len(search_results) == 0:
            return HttpResponse('未找到与"{}"相关鱼类信息。'.format(name))
        return render(request, "fishbaike_search.html", {"results": search_results})
    return HttpResponse("访问方式错误，请使用GET请求访问。")


def fishbaike_showdetail(request: HttpRequest):
    with open("./information/per", "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            uid = int(line)

    user = User.objects.get(id=uid)

    if request.method == "GET":
        name = request.GET.get("name")
        print(name)
        filter_result = FishBaike.objects.filter(name=name)
        if len(filter_result) == 0:
            return HttpResponse("未找到该鱼类({})的信息。".format(name))
        if len(filter_result) > 1:
            return HttpResponse(
                "数据库中存在多个名为{}的鱼类，请联系管理员解决。".format(name)
            )
        fishbaike = filter_result[0]
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        RELA_DIR = "model/data/fish/baike"
        baike_dir = os.path.join(BASE_DIR, RELA_DIR)
        all_pics = os.listdir(os.path.join(baike_dir, "pics"))
        images = [
            settings.STATIC_URL + "fish/baike/pics/" + pic
            for pic in all_pics
            if pic.startswith(name)
        ]
        return render(
            request,
            "fishbaike_detail.html",
            {
                "fish_info": {
                    "name": fishbaike.name,
                    "alias": fishbaike.alias,
                    "distribution": fishbaike.distribution,
                    "food": fishbaike.food,
                    "appearance": fishbaike.appearance.split("\n"),
                    "brief_intro": fishbaike.brief_intro.split("\n"),
                    "images": images,
                    "permission": user.permission,
                }
            },
        )
    return HttpResponse("访问方式错误，请使用GET请求访问。")


def fishbaike_exportdata(request: HttpRequest):
    org_fishinfos = FishBaike.objects.all()
    fishinfos: dict[str:dict] = {}
    for fishinfo in org_fishinfos:
        fishinfos[fishinfo.name] = {
            "alias": fishinfo.alias,
            "distribution": fishinfo.distribution,
            "food": fishinfo.food,
            "appearance": fishinfo.appearance.split("\n"),
            "brief_intro": fishinfo.brief_intro.split("\n"),
        }
    json_data = json.dumps(fishinfos, indent=2, ensure_ascii=False)
    response = HttpResponse(json_data, content_type="application/json")
    response["Content-Disposition"] = 'attachment; filename="export.json"'
    return response


#############################################
# 天气更新
#############################################
def weather_get_all_citys() -> dict[str : list[str]]:
    """{省份: [城市1, 城市2, ...]}"""
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    weather_data_dir = os.path.join(BASE_DIR, "model/data/weather")
    weather_city_infos_path = os.path.join(weather_data_dir, "city_infos.json")
    if not os.path.isfile(weather_city_infos_path):
        # 不存在城市信息则爬取
        city_infos = get_city_infos(weather_city_infos_path)
    else:
        with open(weather_city_infos_path, "r", encoding="utf-8") as rfp:
            city_infos: dict[str : list[str]] = json.load(rfp)
    return city_infos


def weather_get_cur_loc() -> tuple[str, str]:
    """当前省市"""
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    weather_data_dir = os.path.join(BASE_DIR, "model/data/weather")
    current_city_path = os.path.join(weather_data_dir, "current_city.json")
    cur_loc: dict[str:str] = {}  # 当前省市
    if not os.path.isfile(current_city_path):
        all_citys = weather_get_all_citys()
        provs = list(all_citys.keys())
        cur_loc = {
            "province": provs[0],
            "city": all_citys[provs[0]][0],
        }
        with open(current_city_path, "w", encoding="utf-8") as wfp:
            json.dump(cur_loc, wfp, ensure_ascii=False)
    else:
        with open(current_city_path, "r", encoding="utf-8") as rfp:
            cur_loc = json.load(rfp)
    return cur_loc["province"], cur_loc["city"]


def weather_get_cur_loc_weather_data(
    force_up_to_date: bool = False,
) -> tuple[str, str, list[dict], list[list[dict]]]:
    """
    当前省市及其未来七天每日天气与每日每3h天气
    - force_up_to_date为True表示强制爬取
    """
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    weather_data_dir = os.path.join(BASE_DIR, "model/data/weather")
    cur_province, cur_city = weather_get_cur_loc()
    weather_file = os.path.join(
        weather_data_dir, "weather-{}-{}.json".format(cur_province, cur_city)
    )
    use_spider = force_up_to_date
    weather_days: list[dict] = []
    weather_hours: list[list[dict]] = []
    if not use_spider and os.path.isfile(weather_file):
        with open(weather_file, "r", encoding="utf-8") as rfp:
            weather_infos = json.load(rfp)
        weather_days, weather_hours = weather_infos["day"], weather_infos["hour"]
        cur_date = datetime.today().strftime("%m/%d")
        if weather_days[-1]["date"] < cur_date:
            use_spider = True
    else:
        use_spider = True
    if use_spider:
        weather_days, weather_hours = get_weather_infos(
            cur_province, cur_city, weather_file
        )
    return cur_province, cur_city, weather_days, weather_hours


def weather_weekreport(request: HttpRequest):
    cur_prov, cur_city, weather_days, weather_hours = weather_get_cur_loc_weather_data()
    target_id = request.GET.get("id")
    if target_id is not None:
        target_id = int(target_id) - 1
        weather_hours = weather_hours[target_id]
    else:
        weather_hours = None
    return render(
        request,
        "weather_detail.html",
        {
            "cur_prov": cur_prov,
            "cur_city": cur_city,
            "weather_days": weather_days,
            "weather_hours": weather_hours,
        },
    )


def weather_changeloc(request: HttpRequest):
    if request.method == "GET":
        all_citys = weather_get_all_citys()
        cur_prov, cur_city = weather_get_cur_loc()
        return render(
            request,
            "weather_changeloc.html",
            {
                "cur_prov": cur_prov,
                "cur_city": cur_city,
                "prov_city_dict": all_citys,
            },
        )
    else:
        new_loc = request.POST.get("city")
        new_prov, new_city = new_loc.split("-")
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        weather_data_dir = os.path.join(BASE_DIR, "model/data/weather")
        current_city_path = os.path.join(weather_data_dir, "current_city.json")
        with open(current_city_path, "w", encoding="utf-8") as wfp:
            json.dump({"province": new_prov, "city": new_city}, wfp, ensure_ascii=False)
        return redirect("http://localhost:8000/system/AIcenter.html")


def weather_fresh(request: HttpRequest):
    weather_get_cur_loc_weather_data(True)
    return redirect("http://127.0.0.1:8000/system/AIcenter.html")


