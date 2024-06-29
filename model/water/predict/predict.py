from .getdata import WaterDataset, getdata_from_xlsx
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.utils.data import Dataset
from .ResMLP import ResMLP

water_predict_list = {"0": "Ⅰ", "1": "ⅠⅠ", "2": "ⅠⅠⅠ", "3": "ⅠV", "4": "劣V"}


def premanage(data):
    # 采用地表水水质评价指标

    out_dict = {0: "I", 1: "II", 2: "III", 3: "IV", 4: "V"}
    error = []

    # 水温
    if data[0] > 0 and data[0] < 20:
        error.append(0)
    elif data[0] < 30:
        error.append(2)
    else:
        error.append(4)

    # PH
    if data[1] > 6 and data[1] < 9:
        error.append(0)
    else:
        error.append(4)

    # 溶氧量
    if data[2] is None:
        error.append(0)
    elif data[2] >= 7.5:
        error.append(0)
    elif data[2] >= 6:
        error.append(1)
    elif data[2] >= 5:
        error.append(2)
    elif data[2] >= 3:
        error.append(3)
    else:
        error.append(4)

    # 高锰酸
    if data[5] is None:
        error.append(0)
    elif data[5] <= 2:
        error.append(0)
    elif data[5] <= 4:
        error.append(1)
    elif data[5] <= 6:
        error.append(2)
    elif data[5] <= 10:
        error.append(3)
    else:
        error.append(4)

    # an氮
    if data[6] is None:
        error.append(0)
    elif data[6] <= 0.15:
        error.append(0)
    elif data[6] <= 0.5:
        error.append(1)
    elif data[6] <= 1:
        error.append(2)
    elif data[6] <= 1.5:
        error.append(3)
    else:
        error.append(4)

    # 磷
    if data[7] is None:
        error.append(0)
    elif data[7] <= 0.02:
        error.append(0)
    elif data[7] <= 0.1:
        error.append(1)
    elif data[7] <= 0.2:
        error.append(2)
    elif data[7] <= 0.3:
        error.append(3)
    else:
        error.append(4)

    # 总氮
    if data[8] is None:
        error.append(0)
    elif data[8] <= 0.2:
        error.append(0)
    elif data[8] <= 0.5:
        error.append(1)
    elif data[8] <= 1.0:
        error.append(2)
    elif data[8] <= 1.5:
        error.append(3)
    else:
        error.append(4)

    count = [0, 0, 0, 0, 0]
    for i in error:
        count[i] += 1
    return error, count


def model_predict(
    data,
    count,
    path="./model/water/predict/model.pth",
    in_dim=7,
    out_dim=5,
    device="cpu",
    need=False,
):
    model = ResMLP(in_dim, out_dim)
    model.load_state_dict(torch.load(path, map_location=torch.device("cpu")))
    model = model.to(device)
    model.eval()

    if need:
        data = premanage(data)
    data = torch.tensor(data).float().to(device)
    data = data.view(-1, 7)
    # print(data.shape)
    output = model(data)
    pred = output.data.max(1)[1]

    res = 0

    for i in range(5):
        if count[i] != 0:
            res = i

    return pred, str(res)
