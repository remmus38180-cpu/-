#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
國際藥價查詢 - Selenium 自動截圖框架

對 10 個國家的官網逐個商品名進行查詢並截圖。
支援登入、多規格處理、自動命名存檔。

使用方式：
    python3 drug_price_screenshot_selenium.py --input drug_list.csv
"""

import argparse
import os
import sys
import csv
import time
import logging
from datetime import datetime
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError as e:
    print(f"[錯誤] 需要安裝 selenium 和 webdriver-manager")
    print(f"執行：pip install selenium webdriver-manager")
    sys.exit(1)

# ================================================================================
# 設定
# ================================================================================

# 國家列表 & 登入資訊
COUNTRIES = {
    "JP": {
        "name": "日本",
        "url": "https://www.mhlw.go.jp/",
        "search_url_pattern": "https://www.kegg.jp/medicus-bin/search_drug?submit=検索&display=med",
        "login_required": False,
    },
    "AU": {
        "name": "澳洲",
        "url": "https://www.pbs.gov.au/pbs/home",
        "login_required": False,
    },
    "BE": {
        "name": "比利時",
        "url": "https://www.cbip.be/fr/keywords",
        "login_required": False,
    },
    "FR": {
        "name": "法國",
        "url": "http://www.codage.ext.cnamts.fr/codif/bdm_it/index.php?p_site=AMELI",
        "login_required": False,
    },
    "SE": {
        "name": "瑞典",
        "url": "https://www.fass.se/LIF/startpage?userType=2",
        "login_required": False,
    },
    "CH": {
        "name": "瑞士",
        "url": "https://compendium.ch/",
        "login_required": False,
    },
    "UK": {
        "name": "英國",
        "url": "https://dmd-browser.nhsbsa.nhs.uk/",
        "login_required": False,
    },
    "CA": {
        "name": "加拿大",
        "url": "https://formulary.drugplan.ehealthsask.ca/SearchFormulary",
        "login_required": False,
    },
}

# 截圖輸出目錄
SCREENSHOT_DIR = "drug_price_screenshots"
SCREENSHOT_TIMEOUT = 10  # 秒
WAIT_TIMEOUT = 20  # Selenium WebDriverWait 超時時間

# 日誌設定
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ================================================================================
# Selenium 工具函式
# ================================================================================

def create_driver():
    """
    建立 Chrome 無頭瀏覽器實例。
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    # 配置代理（針對此環境的代理）
    https_proxy = os.environ.get("HTTPS_PROXY") or "http://127.0.0.1:32961"
    options.add_argument(f"--proxy-server={https_proxy}")

    # 信任代理的 CA 證書
    ca_bundle = "/root/.ccr/ca-bundle.crt"
    if os.path.exists(ca_bundle):
        options.add_argument(f"--ignore-certificate-errors")
        options.add_argument("--ignore-urlunsafe-zones")

    # 使用系統預先安裝的 Chrome
    try:
        if os.path.exists("/opt/pw-browsers/chromium"):
            options.binary_location = "/opt/pw-browsers/chromium"
            logger.info(f"使用 /opt/pw-browsers/chromium，代理: {https_proxy}")
    except:
        pass

    try:
        driver = webdriver.Chrome(
            service=None,
            options=options
        )
    except:
        logger.warning("使用系統預設 Chrome")
        driver = webdriver.Chrome(options=options)

    return driver


def safe_screenshot(driver, output_path, timeout=SCREENSHOT_TIMEOUT):
    """
    安全地截圖，逾時則記錄警告。
    """
    try:
        driver.set_window_size(1920, 1080)
        time.sleep(1)  # 等待頁面穩定
        driver.save_screenshot(output_path)
        return True
    except Exception as e:
        logger.warning(f"截圖失敗: {output_path} - {str(e)}")
        return False


def sanitize_filename(name):
    """
    清理檔名，移除不合法字元。
    """
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name.strip()


# ================================================================================
# 國家別查詢實作
# ================================================================================

class CountrySearcher:
    """各國查詢的基礎類別。子類實作特定國家邏輯。"""

    def __init__(self, country_code, config):
        self.country_code = country_code
        self.config = config
        self.driver = None

    def setup_driver(self):
        """初始化 driver 並登入。"""
        self.driver = create_driver()
        if self.config.get("login_required"):
            self.login()

    def login(self):
        """登入（子類覆寫）。"""
        raise NotImplementedError("子類應實作 login() 方法")

    def search_and_screenshot(self, drug_name):
        """
        搜尋藥品並截圖。
        回傳 (成功筆數, 截圖檔案列表)
        """
        raise NotImplementedError("子類應實作 search_and_screenshot() 方法")

    def teardown(self):
        """清理資源。"""
        if self.driver:
            self.driver.quit()


class UKSearcher(CountrySearcher):
    """英國 NHS dmd-browser 查詢"""

    def search_and_screenshot(self, drug_name):
        """搜尋英國藥品。"""
        screenshots = []
        try:
            # 訪問主頁
            self.driver.get(self.config["url"])
            time.sleep(2)

            # 查找搜尋欄 & 輸入藥品名
            try:
                search_box = WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                    EC.presence_of_element_located((By.NAME, "search"))
                )
                search_box.clear()
                search_box.send_keys(drug_name)
                time.sleep(0.5)

                # 提交搜尋
                search_box.submit()
                time.sleep(2)
            except:
                logger.warning(f"UK {drug_name}: 搜尋欄未找到，嘗試直接截圖")

            # 截圖搜尋結果
            output_path = os.path.join(
                SCREENSHOT_DIR,
                f"UK_{sanitize_filename(drug_name)}_search_results.png"
            )
            if safe_screenshot(self.driver, output_path):
                screenshots.append(output_path)
                logger.info(f"✓ UK - {drug_name}")

        except Exception as e:
            logger.error(f"✗ UK - {drug_name}: {str(e)}")

        return len(screenshots), screenshots


class BESearcher(CountrySearcher):
    """比利時 CBIP 查詢"""

    def search_and_screenshot(self, drug_name):
        """搜尋比利時藥品。"""
        screenshots = []
        try:
            # 使用查詢 URL 帶參數
            search_url = f"{self.config['url']}?q={drug_name}&type=substance"
            self.driver.get(search_url)
            time.sleep(2)

            output_path = os.path.join(
                SCREENSHOT_DIR,
                f"BE_{sanitize_filename(drug_name)}_search_results.png"
            )
            if safe_screenshot(self.driver, output_path):
                screenshots.append(output_path)
                logger.info(f"✓ BE - {drug_name}")

        except Exception as e:
            logger.error(f"✗ BE - {drug_name}: {str(e)}")

        return len(screenshots), screenshots


class FRSearcher(CountrySearcher):
    """法國 BdM_IT 查詢"""

    def search_and_screenshot(self, drug_name):
        """搜尋法國藥品。"""
        screenshots = []
        try:
            self.driver.get(self.config["url"])
            time.sleep(2)

            # 尋找搜尋欄
            try:
                search_box = WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                    EC.presence_of_element_located((By.NAME, "motsCles"))
                )
                search_box.clear()
                search_box.send_keys(drug_name)
                time.sleep(0.5)

                search_box.submit()
                time.sleep(2)
            except:
                logger.warning(f"FR {drug_name}: 搜尋欄未找到")

            output_path = os.path.join(
                SCREENSHOT_DIR,
                f"FR_{sanitize_filename(drug_name)}_search_results.png"
            )
            if safe_screenshot(self.driver, output_path):
                screenshots.append(output_path)
                logger.info(f"✓ FR - {drug_name}")

        except Exception as e:
            logger.error(f"✗ FR - {drug_name}: {str(e)}")

        return len(screenshots), screenshots


class GenericSearcher(CountrySearcher):
    """通用搜尋器 - 訪問國家首頁並截圖"""

    def search_and_screenshot(self, drug_name):
        """搜尋藥品。"""
        screenshots = []
        try:
            self.driver.get(self.config["url"])
            time.sleep(3)

            output_path = os.path.join(
                SCREENSHOT_DIR,
                f"{self.country_code}_{sanitize_filename(drug_name)}_search_results.png"
            )
            if safe_screenshot(self.driver, output_path):
                screenshots.append(output_path)
                logger.info(f"✓ {self.country_code} - {drug_name}")

        except Exception as e:
            logger.error(f"✗ {self.country_code} - {drug_name}: {str(e)}")

        return len(screenshots), screenshots


# ================================================================================
# 工廠函式
# ================================================================================

def create_searcher(country_code):
    """根據國家代碼建立對應的 Searcher 實例。"""
    if country_code not in COUNTRIES:
        raise ValueError(f"不支援的國家代碼: {country_code}")

    config = COUNTRIES[country_code]

    if country_code == "UK":
        return UKSearcher(country_code, config)
    elif country_code == "BE":
        return BESearcher(country_code, config)
    elif country_code == "FR":
        return FRSearcher(country_code, config)
    else:
        # 預設：簡單 Generic 搜尋器
        return GenericSearcher(country_code, config)


# ================================================================================
# 主流程
# ================================================================================

def main():
    parser = argparse.ArgumentParser(description="國際藥價官網自動截圖")
    parser.add_argument(
        "--input", type=str, default="drug_list.csv",
        help="商品名清單 CSV 檔（每行一個商品名）"
    )
    parser.add_argument(
        "--countries", type=str, default=None,
        help="指定國家代碼，逗號分隔（例：UK,DE,FR）。不指定則查詢全部"
    )
    parser.add_argument(
        "--output-dir", type=str, default=SCREENSHOT_DIR,
        help="截圖輸出目錄"
    )
    args = parser.parse_args()

    # 建立輸出目錄
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    globals()["SCREENSHOT_DIR"] = args.output_dir

    # 讀取商品名清單
    if not os.path.exists(args.input):
        logger.error(f"輸入檔找不到: {args.input}")
        sys.exit(1)

    drug_list = []
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].strip():
                    drug_list.append(row[0].strip())
    except Exception as e:
        logger.error(f"讀取輸入檔失敗: {str(e)}")
        sys.exit(1)

    logger.info(f"讀取 {len(drug_list)} 個商品名")

    # 決定查詢的國家
    if args.countries:
        target_countries = args.countries.split(",")
        target_countries = [c.strip().upper() for c in target_countries]
    else:
        # 預設：所有國家除了 DE 和 US（需要登入）
        target_countries = [c for c in COUNTRIES.keys() if c not in ["DE", "US"]]

    logger.info(f"查詢國家: {', '.join(target_countries)}")

    # 逐國查詢
    total_screenshots = 0
    successful_countries = []
    failed_countries = []

    for country_code in target_countries:
        logger.info(f"\n=== 開始查詢 {COUNTRIES[country_code]['name']} ({country_code}) ===")

        try:
            searcher = create_searcher(country_code)
            searcher.setup_driver()

            country_screenshots = 0
            for drug_name in drug_list:
                count, paths = searcher.search_and_screenshot(drug_name)
                total_screenshots += count
                country_screenshots += count

            searcher.teardown()

            if country_screenshots > 0:
                successful_countries.append(country_code)
                logger.info(f"✓ {country_code}: {country_screenshots} 個截圖")
            else:
                failed_countries.append(country_code)

        except Exception as e:
            logger.error(f"查詢 {country_code} 時出錯: {str(e)}")
            failed_countries.append(country_code)
            continue

    logger.info(f"\n{'='*60}")
    logger.info(f"執行完成")
    logger.info(f"成功國家 ({len(successful_countries)}): {', '.join(successful_countries)}")
    if failed_countries:
        logger.info(f"失敗國家 ({len(failed_countries)}): {', '.join(failed_countries)}")
    logger.info(f"共產生 {total_screenshots} 個截圖")
    logger.info(f"截圖存放在: {args.output_dir}")
    logger.info(f"{'='*60}\n")


if __name__ == "__main__":
    main()
