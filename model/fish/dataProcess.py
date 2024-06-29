import pandas as pd
import numpy as np
import os,json

DATA_DIR = '../data/fish'
OUT_DIR = '../data/fish/processed'

'''
    Year：收集样本的日历年份，如1992
    Date：收集样本的日期，如1992/7/21
    Latin_Name：基于AFS鱼类名称，第6版，2004年的每个类群的科学名称
    Temp_C：样本收集时的水温（摄氏度）
    Count：在样本中收集的每个类群的每个大小类别的个体总数
    3cm_Size_Class：每个个体的3厘米大小范围，如33.1 - 36.0
    Weight_kg：在样本中收集的每个类群的每个大小类别（或长度）的所有个体的总重量
'''

columns = ['Year', 'Date', 'Latin_Name', 'Count', '3cm_Size_Class', 'Weight_kg']
files = [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if f.endswith('.xlsx')]
TOP5 = ['Aplodinotus grunniens', 'Ictalurus punctatus', 'Dorosoma cepedianum', 'Sander canadensis', 'Lepomis macrochirus']

# 提取四个excel的数据，合并到一个csv中
def extract_data():
    df = pd.DataFrame(columns=columns)
    for file in files:
        sheet = 1 if file.split('/')[-1].startswith('Ohio') else 0
        df = pd.concat([df, pd.read_excel(file, sheet_name=sheet,usecols=columns)], ignore_index=True, axis=0)
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)
    df.to_csv(os.path.join(OUT_DIR, 'fish.csv'))

# 数据清洗
def clean_data():
    df = pd.read_csv(os.path.join(OUT_DIR, 'fish.csv'))
    # 删除缺失值和重复值
    df.dropna(inplace=True)
    df.drop_duplicates(inplace=True)
    # 删除异常值
    df = df[df['Count'] > 0]
    df = df[df['Weight_kg'] > 0]
    # 新增两列，存储某鱼群体长和体重的平均值
    df['Mean_Length'] = df['3cm_Size_Class'].apply(lambda x: (float(x.split('-')[0]) + float(x.split('-')[1])) / 2)
    df['Mean_Weight'] = df['Weight_kg'] / df['Count']
    # 按照日期排序
    df['Date'] = pd.to_datetime(df['Date'])
    df.sort_values(by='Date', inplace=True)
    # 重置索引
    df.reset_index(drop=True, inplace=True)
    df.pop('Unnamed: 0')
    df.to_csv(os.path.join(OUT_DIR, 'fish_cleaned.csv'))

# 由于上述处理后的数据，有很多日期相同，名字相同的数据，这里对这些数据进一步合并
def process_data(onlyTop3=True):
    df = pd.read_csv(os.path.join(OUT_DIR, 'fish_cleaned.csv'),index_col=0)
    all_group = df.groupby(['Date', 'Latin_Name'])
    df_final = pd.DataFrame(columns=['Year', 'Date', 'Latin_Name', 'Count', 'Mean_Length', 'Mean_Weight'])
    # 对每个分组，计算平均体长和平均体重
    for group_name in all_group.groups:
        curr_group = np.array(all_group.get_group(group_name))
        count = sum(curr_group[:,-5])
        mean_weight = sum(curr_group[:, -1] * curr_group[:,-5]) / count
        mean_length = sum(curr_group[:, -2] * curr_group[:,-5]) / count
        row = curr_group[0].tolist()[:3]
        row.extend([count, mean_length, mean_weight])
        df_final = pd.concat([df_final, pd.DataFrame([row], columns=df_final.columns)], ignore_index=True, axis=0)
    df_final['Date'] = pd.to_datetime(df_final['Date'])
    if onlyTop3:
        top3 = getTop3()
        df_final = df_final[df_final['Latin_Name'].isin(top3)]
        df_final.reset_index(drop=True, inplace=True)
    df_final.to_csv(os.path.join(OUT_DIR, 'fish_final.csv'))

# 找到日期数据最多的三个鱼类，用于构建LSTM
def getTop3():
    data = pd.read_csv(os.path.join(OUT_DIR, 'fish_cleaned.csv'),index_col=0)
    all_groups = data.groupby('Latin_Name')
    tuples = []
    for group_name in all_groups.groups:
        curr_group = all_groups.get_group(group_name)
        dates = curr_group['Date'].unique()
        tuples.append((group_name, len(dates)))
    tuples.sort(key=lambda x: x[1], reverse=True)
    return [t[0] for t in tuples[:5]]

# 把数据按照时间进行切分
def split_with_time(interval=40):
    data = pd.read_csv(os.path.join(OUT_DIR, 'fish.csv'),index_col=0)
    data['Date'] = pd.to_datetime(data['Date'])
    data.sort_values(by='Date', inplace=True)
    max_time = data['Date'].max()
    min_time = data['Date'].min()
    # 切成60个接近相等的时间段
    time_interval = (max_time - min_time) / interval
    time_list = [min_time + i * time_interval for i in range(1, interval+1)]
    # 按照时间切分，统计这段时间内的鱼群总量
    count = 0
    count_list = []
    for i in range(interval):
        if i == interval-1:
            df = data[data['Date'] >= time_list[i]]
            time = max_time
        else:
            df = data[(data['Date'] >= time_list[i]) & (data['Date'] < time_list[i + 1])]
            time = time_list[i]

        count += df['Count'].sum()
        time = pd.to_datetime(time.strftime('%Y-%m'))
        count_list.append((time,int(count)))
    count_list = pd.DataFrame(count_list,columns=['Date','Count'])
    count_list.to_csv(os.path.join(OUT_DIR, 'fish_time.csv'))
    return count_list

def get_top_info():
    data = pd.read_csv(os.path.join(OUT_DIR, 'fish_cleaned.csv'), index_col=0)
    top_group = [data.groupby('Latin_Name').get_group(name) for name in TOP5]

    # 均分成六个区间
    weight_list = [0.01,0.05,0.1,0.5,1,3]
    length_list = [5,10,20,30,50,80]

    info = []
    # 统计每个组处在哪个区间的总数
    for group in top_group:
        weight_count_list, length_count_list = [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]
        weight = group['Mean_Weight'].values
        length = group['Mean_Length'].values
        count_list = group['Count'].values

        for i in range(len(weight)):
            for j in range(1,6):
                if weight[i] < weight_list[j]:
                    weight_count_list[j-1] += count_list[i]
                    break
                elif weight[i] < weight_list[0]:
                    weight_count_list[0] += count_list[i]
                elif weight[i] > weight_list[5]:
                    weight_count_list[5] += count_list[i]

        for i in range(len(length)):
            for j in range(1,6):
                if length[i] < length_list[j]:
                    length_count_list[j-1] += count_list[i]
                    break
                elif length[i] < length_list[0]:
                    length_count_list[0] += count_list[i]
                elif length[i] > length_list[5]:
                    length_count_list[5] += count_list[i]

        info.append({'name':group['Latin_Name'].values[0],'weight':weight_count_list,'length':length_count_list})

    with open(os.path.join(OUT_DIR, 'top_info.json'),'w') as f:
        json.dump(info,f,indent=4)



if __name__ == '__main__':
    extract_data()
    clean_data()
    process_data()
    print(getTop3())
    split_with_time()
    get_top_info()

