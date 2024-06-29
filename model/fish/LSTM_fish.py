import pandas as pd
import numpy as np
import torch,os
import torch.nn as nn
from sklearn import model_selection
from sklearn.preprocessing import MinMaxScaler

DATA_PATH = "../data/fish/processed/fish_final.csv"
SAVE_PATH = "../data/fish/save"
TOP3 = ['Aplodinotus grunniens', 'Ictalurus punctatus', 'Dorosoma cepedianum']
device = torch.device('cuda')

# 获取单一的鱼类数据
def get_fish_data(fish_name):
    df = pd.read_csv(DATA_PATH, index_col=0)
    df = df[df['Latin_Name'] == fish_name]
    df.pop('Latin_Name')
    df.reset_index(drop=True, inplace=True)
    return df

def train_test_split(data):
    data['Date'] = pd.to_datetime(data['Date'])
    data['Date_ordinal'] = data['Date'].apply(lambda x: x.toordinal())
    features = data[['Year', 'Date_ordinal', 'Count']] # 特征
    target = data[['Mean_Length', 'Mean_Weight']] # 目标
    scaler_X,scaler_Y = MinMaxScaler(),MinMaxScaler()
    features = scaler_X.fit_transform(features)
    target = scaler_Y.fit_transform(target)

    # 构建输入输出序列
    sequence_length = 10
    X,Y = [], []
    for i in range(len(features) - sequence_length):
        X.append(features[i:i + sequence_length])
        Y.append(target[i + sequence_length])
    X,Y = np.array(X),np.array(Y)
    X_train, X_test, Y_train, Y_test = model_selection.train_test_split(X, Y, test_size=0.1, random_state=42)

    X_train = torch.tensor(X_train, dtype=torch.float32)
    Y_train = torch.tensor(Y_train, dtype=torch.float32)
    X_test = torch.tensor(X_test, dtype=torch.float32)
    Y_test = torch.tensor(Y_test, dtype=torch.float32)
    return X_train,Y_train,X_test,Y_test,scaler_X,scaler_Y


class LSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, output_size):
        super(LSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)

        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out

class LSTMModel():
    def __init__(self, input_size, hidden_size, num_layers, output_size,SAVE_PATH=SAVE_PATH):
        self.model1 = LSTM(input_size, hidden_size, num_layers, output_size).to(device)
        self.model2 = LSTM(input_size, hidden_size, output_size, num_layers).to(device)
        self.model3 = LSTM(input_size, hidden_size, output_size, num_layers).to(device)
        self.rates = [0.34, 0.33, 0.33]

        self.model1.load_state_dict(torch.load(f'{SAVE_PATH}/fish_0.pth'))
        self.model2.load_state_dict(torch.load(f'{SAVE_PATH}/fish_1.pth'))
        self.model3.load_state_dict(torch.load(f'{SAVE_PATH}/fish_2.pth'))

    def api(self, X_test,DATA_PATH=DATA_PATH):
        X_test = torch.tensor(X_test, dtype=torch.float32).to(device)
        self.model1.eval()
        self.model2.eval()
        self.model3.eval()
        with torch.no_grad():
            predictions1 = self.model1(X_test)
            predictions2 = self.model2(X_test)
            predictions3 = self.model3(X_test)
        predictions = self.rates[0] * predictions1 + self.rates[1] * predictions2 + self.rates[2] * predictions3
        scaler = MinMaxScaler()
        scaler.fit(pd.read_csv(DATA_PATH, index_col=0)[['Mean_Length', 'Mean_Weight']])
        predictions = scaler.inverse_transform(np.abs(predictions.cpu().numpy()))
        return predictions[0]

def generate_wave_numbers(start, end, num_points=8, amplitude=1, frequency=1):
    if end - start > 15:
        end = end - 15
    linear_points = np.linspace(start, end, num_points + 2)
    wave = amplitude * np.sin(np.linspace(0, frequency * np.pi, num_points + 2))
    wave_points = linear_points + wave
    return list(wave_points)

if __name__ == '__main__':
    data = pd.read_csv(DATA_PATH, index_col=0)
    data = data[data['Latin_Name'] == 'Dorosoma cepedianum']
    data['Date'] = pd.to_datetime(data['Date'])
    data['Date_ordinal'] = data['Date'].apply(lambda x: x.toordinal())
    data = data[['Year', 'Date_ordinal', 'Count']]
    data = np.array(data)
    data = data[-10:]
    data = np.expand_dims(data, axis=0)
    model = LSTMModel(3,100,2,2,SAVE_PATH=SAVE_PATH)
    data = model.api(data)
    print(data)