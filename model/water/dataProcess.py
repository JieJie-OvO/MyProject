import pandas as pd
import numpy as np
import os,json

DATA_DIR = '../data/water'
OUT_DIR = '../data/water/processed'

'''
    Date:日期
    temp:温度
    pH:pH值
    Ox:含氧量
    Dao:导电率
    Zhuodu:浊度
    Yandu:盐度
    Andan:氨氮
    Zonglin:总磷
    Zongdan:总氮
'''
# 数据导入
def extract_data():
    file = '../data/water/水质数据.xlsx'
    df = pd.read_excel(file, names = ['Date', 'temp', 'pH', 'Ox', 'Dao', 'Zhuodu', 'Yandu', 'Andan', 'Zonglin', 'Zongdan'], usecols = [0, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    df.to_csv(os.path.join(OUT_DIR, 'water.csv'))

# 数据处理
def clean_data():
    df=pd.read_csv(os.path.join(OUT_DIR, 'water.csv'))
    #删除空项
    df=df.dropna()
    #删除非法项
    for i in ['Date', 'temp', 'pH', 'Ox', 'Dao', 'Zhuodu', 'Yandu', 'Andan', 'Zonglin', 'Zongdan']:
        df=df.drop(df[df[i]=='--'].index)
    #类型转换
    df=df.astype('float64')
    #保存
    df.to_csv(os.path.join(OUT_DIR, 'water_cleaned.csv'))

# 地图水质数据导入
# 忽略流域与河流名，直接为每个省份导出一个csv文件:省名.csv
# csv文件格式如下
'''
    Province:省名
    Date:日期
    Class:水质等级
    temp:温度
    pH:pH值
    Ox:含氧量
    Dao:导电率
    Zhuodu:浊度
    Yandu:盐度
    Andan:氨氮
    Zonglin:总磷
    Zongdan:总氮
'''
def extract_map():
    frame=['Province', 'Class', 'temp', 'pH', 'Ox', 'Dao', 'Zhuodu', 'Yandu', 'Andan', 'Zonglin', 'Zongdan']
    # 全国平均数据
    all_df=pd.DataFrame(columns=frame)
    # 列名
    columns = ['Province', 'Date', 'Class', 'temp', 'pH', 'Ox', 'Dao', 'Zhuodu', 'Yandu', 'Andan', 'Zonglin', 'Zongdan']
    # 文件目录
    dir_path='../data/water/水质数据（补充）/water_quality_by_name'
    # 省级目录列表
    province_list=os.listdir(dir_path)
    for p in province_list:
        #用于合并的csv列表
        data_list=[]
        #省级目录
        province_path=os.path.join(dir_path,p)
        #流域目录列表
        basin_list=os.listdir(province_path)
        for b in basin_list:
            #流域目录
            basin_path=os.path.join(province_path,b)
            #河流目录列表
            site_list=os.listdir(basin_path)
            for s in site_list:
                #河流目录
                site_path=os.path.join(basin_path,s)
                #时间目录列表（事实上只有2021-4的数据）
                time_list=os.listdir(site_path)
                for t in time_list:
                    #时间目录
                    time_path=os.path.join(site_path,t)
                    #csv文件列表
                    file_list=os.listdir(time_path)
                    for f in file_list:
                        #csv文件
                        file_path=os.path.join(time_path,f)
                        #筛选数据
                        data=pd.read_csv(file_path,header=0,usecols=[0,3,4,5,6,7,8,9,10,11,12,13],names=columns)
                        #填入列表
                        data_list.append(data)
        #合并csv
        df=pd.concat(data_list,ignore_index=True,axis=0)
        #删去非法数据
        for i in columns:
            df=df.drop(df[df[i]=='--'].index)
            df=df.drop(df[df[i]=='*'].index)
        #将数值类型的列的数据类型转为float
        for i in ['temp', 'pH', 'Ox', 'Dao', 'Zhuodu', 'Yandu', 'Andan', 'Zonglin', 'Zongdan']:
            df[i]=df[i].astype('float64')
        #保存
        out_path=os.path.join(OUT_DIR,'map')
        df.to_csv(os.path.join(out_path, p+'.csv'))
        #处理平均数据
        Class=0
        for i in range(len(df)):
            row=df.iloc[i]
            if row['Class']=='Ⅰ':
                Class=Class+1
            if row['Class']=='Ⅱ':
                Class=Class+2
            if row['Class']=='Ⅲ':
                Class=Class+3
            if row['Class']=='Ⅳ':
                Class=Class+4
            if row['Class']=='Ⅴ':
                Class=Class+5
            if row['Class']=='劣Ⅴ':
                Class=Class+6
        Class=int(round(Class/len(df)+0.5,0))
        Temp=round(df['temp'].mean(),3)
        pH=round(df['pH'].mean(),3)
        Ox=round(df['Ox'].mean(),3)
        Dao=round(df['Dao'].mean(),3)
        Zhuodu=round(df['Zhuodu'].mean(),3)
        Yandu=round(df['Yandu'].mean(),3)
        Andan=round(df['Andan'].mean(),3)
        Zonglin=round(df['Zonglin'].mean(),3)
        Zongdan=round(df['Zongdan'].mean(),3)
        all_df.loc[len(all_df)]=[p,Class,Temp,pH,Ox,Dao,Zhuodu,Yandu,Andan,Zonglin,Zongdan]
    #保存全国平均数据
    out_path=os.path.join(OUT_DIR,'map')
    all_df.to_csv(os.path.join(out_path,'全国.csv'))

if __name__ == '__main__':
    extract_data()
    clean_data()
    extract_map()