from datetime import datetime, timedelta

def date2num(date_str):
    # 定义基准日期
    base_date = datetime(2024, 5, 15)
    
    # 将输入的日期字符串转换为datetime对象
    given_date = datetime.strptime(date_str, '%Y-%m-%d')
    
    # 计算两个日期之间的天数差
    delta = given_date - base_date
    
    # 返回天数差，即自定义的正数
    return delta.days + 45427

def num2date(number):
    # 定义基准日期
    base_date = datetime(2024, 5, 15)
    
    # 将天数差转换为timedelta对象
    delta = timedelta(days=(number-45427))
    
    # 将基准日期加上天数差得到结果日期
    result_date = base_date + delta
    
    # 返回日期的字符串表示
    return result_date.strftime('%Y-%m-%d')