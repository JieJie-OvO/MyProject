####################
# 爬取天气信息      #
####################
import time, os, json, requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from .config import get_edge_driver

data_dir = "weather-data"


def get_city_infos(dump_path: str) -> dict[str, list[str]]:
    """
    返回以省份名为键、城市名列表为值的字典
    """
    driver = get_edge_driver()
    driver.get("https://weather.cma.cn")
    driver.find_element(By.CSS_SELECTOR, "#current-station").click()
    province_select = WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#cityPosition > .dropdown:nth-child(4) > button")
        )
    )
    province_select.click()
    time.sleep(1)
    province_list = driver.find_elements(
        By.CSS_SELECTOR, "#cityPosition > .dropdown:nth-child(4) > ul > li"
    )
    province_names = [province.text for province in province_list]
    province_select.click()  # 第二次点击则会关闭下拉框
    city_infos = {}
    for name, province in zip(province_names, province_list):
        province_select.click()
        time.sleep(1)
        province.click()
        time.sleep(1)
        city_list = driver.find_elements(
            By.CSS_SELECTOR, "#cityPosition > .dropdown:nth-child(6) > ul > li"
        )
        city_infos[name] = [city.text for city in city_list]
    driver.quit()
    json.dump(city_infos, open(dump_path, "w", encoding="utf-8"), ensure_ascii=False)
    return city_infos


def get_weather_infos(
    province_name: str, city_name: str, dump_path: str
) -> tuple[list[dict], list[list[dict]]]:
    """
    返回未来七天的天气信息的字典列表和未来七天每隔3小时的天气信息的字典列表的列表
    - 每天
        - "date"(str): 日期, 如01/01
        - "week"(str): 星期几
        - "weather_beg"(str): 白天天气
        - "weather_end"(str): 晚上天气
        - "wind_direc_beg"(str): 白天风向
        - "wind_direc_end"(str): 晚上风向
        - "wind_level_beg"(str): 白天风力
        - "wind_level_end"(str): 晚上风力
        - "temperature_max"(str): 最高温度
        - "temperature_min"(str): 最低温度
    - 每隔3小时
        - "hour"(str): 时刻
        - "temperature"(str): 温度
        - "rain"(str): 降雨量
        - "wind_veloc"(str): 风速
        - "wind_direc"(str): 风向
        - "pressure"(str): 气压
        - "humidity"(str): 湿度
        - "cloud"(str): 云量
    """
    driver = get_edge_driver()
    driver.get("https://weather.cma.cn/")
    driver.find_element(By.CSS_SELECTOR, "#current-station").click()
    province_select = WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#cityPosition > .dropdown:nth-child(4) > button")
        )
    )
    province_select.click()
    province_list = driver.find_elements(
        By.CSS_SELECTOR, "#cityPosition > .dropdown:nth-child(4) > ul > li"
    )
    weather_day_infos, weather_hour_infos = [], []
    for province in province_list:
        if province.text == province_name:
            province.click()
            time.sleep(1)
            city_list = driver.find_elements(
                By.CSS_SELECTOR, "#cityPosition > .dropdown:nth-child(6) > ul > li > a"
            )
            for city in city_list:
                if city.text == city_name:
                    city_href = city.get_attribute("href")
                    city.click()
                    WebDriverWait(driver, 2).until(EC.url_contains(city_href))
                    dayList_element = driver.find_element(By.CSS_SELECTOR, "#dayList")
                    for index, day_elem in enumerate(
                        dayList_element.find_elements(
                            By.CSS_SELECTOR, "div.pull-left.day"
                        )
                    ):
                        day_elem.click()
                        time.sleep(1)
                        day_items = day_elem.find_elements(
                            By.CSS_SELECTOR, "div.day-item"
                        )
                        weather_day_info = {
                            "date": day_items[0].text,
                            "weather_beg": day_items[2].text,
                            "wind_direc_beg": day_items[3].text,
                            "wind_level_beg": day_items[4].text,
                            "temperature_max": day_items[5]
                            .find_element(By.CSS_SELECTOR, "div.high")
                            .text,
                            "temperature_min": day_items[5]
                            .find_element(By.CSS_SELECTOR, "div.low")
                            .text,
                            "weather_end": day_items[7].text,
                            "wind_direc_end": day_items[8].text,
                            "wind_level_end": day_items[9].text,
                        }
                        for k, v in weather_day_info.items():
                            weather_day_info[k] = v.strip()
                        weather_day_info["week"] = weather_day_info["date"][:3]
                        weather_day_info["date"] = weather_day_info["date"][-5:]
                        weather_day_infos.append(weather_day_info)
                        hourTable = driver.find_element(
                            By.CSS_SELECTOR, f"#hourTable_{index}"
                        )
                        trs = hourTable.find_elements(By.CSS_SELECTOR, "tr")
                        hours = [
                            td.text.strip()
                            for td in trs[0].find_elements(By.CSS_SELECTOR, "td")[1:]
                        ]
                        temperatures = [
                            td.text.strip()
                            for td in trs[2].find_elements(By.CSS_SELECTOR, "td")[1:]
                        ]
                        rains = [
                            td.text.strip()
                            for td in trs[3].find_elements(By.CSS_SELECTOR, "td")[1:]
                        ]
                        wind_velocs = [
                            td.text.strip()
                            for td in trs[4].find_elements(By.CSS_SELECTOR, "td")[1:]
                        ]
                        wind_direcs = [
                            td.text.strip()
                            for td in trs[5].find_elements(By.CSS_SELECTOR, "td")[1:]
                        ]
                        pressures = [
                            td.text.strip()
                            for td in trs[6].find_elements(By.CSS_SELECTOR, "td")[1:]
                        ]
                        humiditys = [
                            td.text.strip()
                            for td in trs[7].find_elements(By.CSS_SELECTOR, "td")[1:]
                        ]
                        clouds = [
                            td.text.strip()
                            for td in trs[8].find_elements(By.CSS_SELECTOR, "td")[1:]
                        ]
                        day_hour_infos = [
                            {
                                "hour": hour,
                                "temperature": temperature,
                                "rain": rain,
                                "wind_veloc": wind_veloc,
                                "wind_direc": wind_direc,
                                "pressure": pressure,
                                "humidity": humidity,
                                "cloud": cloud,
                            }
                            for hour, temperature, rain, wind_veloc, wind_direc, pressure, humidity, cloud in zip(
                                hours,
                                temperatures,
                                rains,
                                wind_velocs,
                                wind_direcs,
                                pressures,
                                humiditys,
                                clouds,
                            )
                        ]
                        weather_hour_infos.append(day_hour_infos)
                    break
            else:
                print(f"{province_name} 不存在 {city_name}")
            break
    else:
        print(f"不存在 {province_name}")
    driver.quit()
    json.dump(
        {
            "province": province_name,
            "city": city_name,
            "day": weather_day_infos,
            "hour": weather_hour_infos,
        },
        open(dump_path, "w", encoding="utf-8"),
        ensure_ascii=False,
        indent=2,
    )
    return weather_day_infos, weather_hour_infos


if __name__ == "__main__":
    os.makedirs(data_dir, exist_ok=True)
    get_city_infos(os.path.join(data_dir, "city_infos.json"))
    # get_weather_infos("天津市", "津南", os.path.join(data_dir, "weather_infos.json"))
