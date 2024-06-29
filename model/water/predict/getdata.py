import pandas as pd
import math
import torch
from torch.utils.data import Dataset, DataLoader


def premanage(data):
    # 采用地表水水质评价指标

    out_dict = {0:'I', 1:'II', 2:'III', 3:'IV', 4:'V'}
    error = []

    # 水温
    if data[0] >0 and data[0]<20:
        error.append(0)
    elif data[0] <30:
        error.append(2)
    else:
        error.append(4)

    # PH
    if data[1]>6 and data[1]<9:
        error.append(0)
    else:
        error.append(4)

    # 溶氧量
    if data[2] is None:
        error.append(0)
    elif data[2]>=7.5:
        error.append(0)
    elif data[2]>=6:
        error.append(1)
    elif data[2]>=5:
        error.append(2)
    elif data[2]>=3:
        error.append(3)
    else:
        error.append(4)

    # 高锰酸
    if data[5] is None:
        error.append(0)
    elif data[5]<=2:
        error.append(0)
    elif data[5]<=4:
        error.append(1)
    elif data[5]<=6:
        error.append(2)
    elif data[5]<=10:
        error.append(3)
    else:
        error.append(4)
    
    # an氮
    if data[6] is None:
        error.append(0)
    elif data[6]<=0.15:
        error.append(0)
    elif data[6]<=0.5:
        error.append(1)
    elif data[6]<=1:
        error.append(2)
    elif data[6]<=1.5:
        error.append(3)
    else:
        error.append(4)

    # 磷
    if data[7] is None:
        error.append(0)
    elif data[7]<=0.02:
        error.append(0)
    elif data[7]<=0.1:
        error.append(1)
    elif data[7]<=0.2:
        error.append(2)
    elif data[7]<=0.3:
        error.append(3)
    else:
        error.append(4)
    
    # 总氮
    if data[8] is None:
        error.append(0)
    elif data[8]<=0.2:
        error.append(0)
    elif data[8]<=0.5:
        error.append(1)
    elif data[8]<=1.0:
        error.append(2)
    elif data[8]<=1.5:
        error.append(3)
    else:
        error.append(4)

    return error 

def getdata_from_xlsx(file_path):
    df = pd.read_excel(file_path)
    df = df.dropna(axis=0, how='any')
    datas = []
    for i in range(len(df)):
        data = df.iloc[i].values.tolist()
        add = True
        for j in range(len(data)):
            t = data[j]
            if type(t) == float:
                if math.isnan(t):
                    add = False
                    break
            elif t == 'nan':
                add = False
                break
            if j>1 and j<11:
                if t == '--':
                    add = False
                    break
        if add:
            datas.append(data)
    return datas

class WaterDataset(Dataset):
    def __init__(self, datas):
        self.datas = datas
    
        '''
        self.min = [10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000]
        self.max = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.delta = []
        for i in range(len(self.datas)):
            for j in range(9):
                self.datas[i][j+2] = float(self.datas[i][j+2])
                self.min[j] = min(self.min[j], self.datas[i][j+2])
                self.max[j] = max(self.max[j], self.datas[i][j+2])
        for i in range(9):
            self.delta.append(max(self.max[i]-self.min[i], 1e-6))
        '''
        for i in range(len(self.datas)):
            for j in range(9):
                self.datas[i][j+2] = float(self.datas[i][j+2])
        
    def __len__(self):
        return len(self.datas)

    def __getitem__(self, idx):
        data = []
        for i in range(9):
            data.append(self.datas[idx][i+2])
        data = premanage(data)

        x = torch.tensor(data).float()

        
        label = 0
        if self.datas[idx][1] == 'Ⅲ':
            label = 2
        elif self.datas[idx][1] == 'Ⅱ':
            label = 1
        elif self.datas[idx][1] == 'Ⅳ':
            label = 3
        elif self.datas[idx][1] == 'Ⅰ':
            label = 0
        elif self.datas[idx][1] == '劣Ⅴ':
            label = 4
        t = torch.tensor(label).long()
        
        return x, t