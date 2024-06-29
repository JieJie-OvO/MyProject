####################
# 爬取鱼类信息及图片 #
####################
import time, os, json, requests
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from .config import get_edge_driver

data_dir = "fish-data"
img_dir = os.path.join(data_dir, "pics")


def get_fish_infos(
    dump_dir: str, interval: float = 1.0, max_num: int = 5
) -> tuple[dict[str:dict], list]:
    """
    爬取鱼类信息及图片链接
    - dump_dir: str, 数据保存目录
    - interval: float, 页面切换间隔(防反爬)，单位秒
    - max_num: int, 最大爬取鱼类种数，-1表示全部爬取
    ---
    返回以鱼名为键、鱼信息为值的字典和获取失败的链接列表，鱼信息包括
        - "images"(list[url])
        - "alias"(str)
        - "distribution"(str)
        - "food"(str)
        - "appearance"(list[str])
        - "brief-intro"(list[str])
    """
    driver = get_edge_driver()
    driver.get("https://www.fishbiji.com/yubaike/")
    fish_list = driver.find_elements(
        By.CSS_SELECTOR,
        "#js-grid-lightbox-trip-finder > div > div div.cbp-item-wrapper",
    )
    action = ActionChains(driver)
    fish_infos, fail_urls = {}, []
    if max_num >= 0 and max_num < len(fish_list):
        fish_list = fish_list[:max_num]
    for fish_item in fish_list:
        fish_pic_url = "https://www.fishbiji.com{}".format(
            fish_item.find_element(By.CSS_SELECTOR, "div.img-box")
            .get_attribute("style")
            .split("url(")[1]
            .split(");")[0][1:-1]
        )
        fish_page = fish_item.find_element(By.CSS_SELECTOR, "div.text-box a")
        action.key_down(Keys.CONTROL).click(fish_page).key_up(Keys.CONTROL).perform()
        driver.switch_to.window(driver.window_handles[-1])
        details = driver.find_elements(By.CSS_SELECTOR, "body div.per-day-trip")
        if len(details) == 3:
            basic_infos = [
                basic_info.text
                for basic_info in details[0].find_elements(
                    By.CSS_SELECTOR, "tbody > tr > td:nth-child(2)"
                )
            ]
            name = basic_infos[0]
            fish_info = {
                "images": list(
                    set(
                        [
                            image.get_attribute("href")
                            for image in driver.find_elements(
                                By.CSS_SELECTOR,
                                "body > div.main-page-wrapper > div.destination-details.mt-120.md-mt-80 > div > div > div > div.col-lg-8.order-lg-1 > div:nth-child(2) > div > div.owl-stage-outer a",
                            )
                        ]
                        + [fish_pic_url]
                    )
                ),
                "alias": basic_infos[1],
                "distribution": basic_infos[2],
                "food": basic_infos[3],
                "appearance": [
                    p.text for p in details[1].find_elements(By.CSS_SELECTOR, "p")
                ],
                "brief-intro": [
                    li.text
                    for li in details[2].find_elements(By.CSS_SELECTOR, "ul > li")
                ],
            }
            fish_infos[name] = fish_info
        time.sleep(interval)
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        if len(details) != 3:
            fail_urls.append(fish_page.get_attribute("href"))
    driver.quit()
    json.dump(
        fish_infos,
        open(os.path.join(dump_dir, "fish_infos.json"), "w", encoding="utf-8"),
        ensure_ascii=False,
        indent=2,
    )
    json.dump(
        fail_urls,
        open(os.path.join(dump_dir, "fail_urls.json"), "w", encoding="utf-8"),
        ensure_ascii=False,
        indent=2,
    )
    return fish_infos, fail_urls


if __name__ == "__main__":
    os.makedirs(data_dir, exist_ok=True)
    fish_infos, fail_urls = get_fish_infos(data_dir)
    # fish_infos = json.load(
    #     open(os.path.join(data_dir, "fish_infos.json"), "r", encoding="utf-8")
    # )
    # fail_urls = json.load(
    #     open(os.path.join(data_dir, "fail_urls.json"), "r", encoding="utf-8")
    # )
    print(
        "{} kinds of fish found and {} urls failed.".format(
            len(fish_infos), len(fail_urls)
        )
    )
    for fail_url in fail_urls:
        print(fail_url)
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
                print(f"{img_name}:{img_url} failed.")
            time.sleep(0.3)
    print(f"{save_cnt:4d}/{total_cnt:4d} images saved.")
