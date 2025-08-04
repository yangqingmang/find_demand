# pray_score.py
# 查找市场评分
import requests
import pandas as pd
import time
import concurrent.futures
from datetime import date, timedelta
from scipy.stats import linregress
from pytrends.request import TrendReq

# 消除 pandas 弃用警告
pd.set_option('future.no_silent_downcasting', True)
# pray_score.py
# 查找市场评分
import requests
import pandas as pd
import time
import concurrent.futures
from datetime import date, timedelta
from scipy.stats import linregress
from pytrends.request import TrendReq

# -------------------------
# 1. 公共指标抓取函数
# -------------------------
WORLD_BANK = "https://api.worldbank.org/v2/country/{}/indicator/{}?format=json&per_page=1"

def get_population(iso2, max_retries=3):
    """互联网人口 = 总人口 * net_users_percent（此处用总人口示例）"""
    for attempt in range(max_retries):
        try:
            resp = requests.get(WORLD_BANK.format(iso2, "SP.POP.TOTL"), timeout=10)
            data = resp.json()
            
            if len(data) > 1 and data[1] and len(data[1]) > 0:
                val = data[1][0].get("value", 0)
                return val or 0
            else:
                print(f"警告: 无法获取 {iso2} 的人口数据")
                if attempt < max_retries - 1:
                    print(f"尝试重试 ({attempt+1}/{max_retries})...")
                    time.sleep(1)  # 等待1秒后重试
                    continue
                return 0
        except Exception as e:
            print(f"获取 {iso2} 人口数据时出错: {e}")
            if attempt < max_retries - 1:
                print(f"尝试重试 ({attempt+1}/{max_retries})...")
                time.sleep(1)  # 等待1秒后重试
                continue
            return 0
    return 0

def get_gdp_per_capita(iso2, max_retries=3):
    """获取人均GDP数据，带重试机制"""
    for attempt in range(max_retries):
        try:
            resp = requests.get(WORLD_BANK.format(iso2, "NY.GDP.PCAP.CD"), timeout=10)
            data = resp.json()
            
            if len(data) > 1 and data[1] and len(data[1]) > 0:
                val = data[1][0].get("value", 0)
                return val or 0
            else:
                print(f"警告: 无法获取 {iso2} 的人均GDP数据")
                if attempt < max_retries - 1:
                    print(f"尝试重试 ({attempt+1}/{max_retries})...")
                    time.sleep(1)
                    continue
                return 0
        except Exception as e:
            print(f"获取 {iso2} 人均GDP数据时出错: {e}")
            if attempt < max_retries - 1:
                print(f"尝试重试 ({attempt+1}/{max_retries})...")
                time.sleep(1)
                continue
            return 0
    return 0

# -------------------------
# 2. Google Ads CPC（占位）
# -------------------------
def get_avg_cpc_usd(keyword: str, geo: str) -> float:
    """
    返回指定国家对某关键词的平均 CPC（美元）
    真实环境需调用 Google Ads API:
    - KeywordPlanIdeaService.GenerateKeywordHistoricalMetrics
    - currency -> USD
    """
    dummy_table = {"US": 1.2, "IN": 0.18, "BR": 0.32, "ID": 0.22}
    return dummy_table.get(geo.upper(), 0.3)

# -------------------------
# 3. Google Trends 增长斜率
# -------------------------
def calc_trend_slope(keyword: str, geo: str, max_retries=3) -> float:
    """
    计算关键词在指定国家的搜索趋势斜率
    添加超时和重试机制
    """
    for attempt in range(max_retries):
        try:
            # 设置较短的超时时间
            pytrend = TrendReq(hl='en-US', tz=360, timeout=(5, 8))
            pytrend.build_payload([keyword], timeframe='today 3-m', geo=geo)  # 缩短时间范围为3个月
            
            # 添加超时处理
            df = pytrend.interest_over_time()
            
            if df.empty:
                print(f"警告: {geo} 的 '{keyword}' 趋势数据为空")
                return 0
                
            y = df[keyword].tolist()
            x = list(range(len(y)))
            
            if len(y) < 2:  # 确保有足够的数据点进行回归
                print(f"警告: {geo} 的 '{keyword}' 趋势数据点不足")
                return 0
                
            slope, *_ = linregress(x, y)
            return slope  # 斜率>0 表示同比增长
        except Exception as e:
            print(f"获取 {geo} 的 '{keyword}' 趋势数据时出错: {e}")
            if attempt < max_retries - 1:
                print(f"尝试重试 ({attempt+1}/{max_retries})...")
                time.sleep(2)  # 等待2秒后重试
                continue
            return 0  # 多次尝试失败后返回0
    return 0

# -------------------------
# 4. P.R.A.Y 评分
# -------------------------
def pray_score(keyword, iso2):
    """计算单个国家的PRAY评分"""
    print(f"正在处理国家: {iso2}...")
    
    p = get_population(iso2)
    r = get_gdp_per_capita(iso2)
    a = get_avg_cpc_usd(keyword, iso2)
    y = calc_trend_slope(keyword, iso2)

    score = 0
    score += 5 if p >= 30_000_000 else 2
    score += 5 if r >= 5000 else 2
    score += 5 if a >= 0.25 else 2
    score += 5 if y > 0 else 1

    result = {
        "country": iso2,
        "population": p,
        "gdp_per_capita": r,
        "avg_cpc": a,
        "trend_slope": round(y, 3),
        "pray_score": score
    }
    
    print(f"完成 {iso2}: 评分 = {score}")
    return result

# -------------------------
# 5. 并行处理函数
# -------------------------
def process_country(args):
    """并行处理单个国家的包装函数"""
    keyword, country = args
    try:
        return pray_score(keyword, country)
    except Exception as e:
        print(f"处理 {country} 时出错: {e}")
        return {
            "country": country,
            "population": 0,
            "gdp_per_capita": 0,
            "avg_cpc": 0,
            "trend_slope": 0,
            "pray_score": 0,
            "error": str(e)
        }

# -------------------------
# 6. 主函数
# -------------------------
if __name__ == "__main__":
    keyword = "ai marketing tool"        # 种子词
    # 使用标准的ISO 2字母国家代码
    country_list = ["US", "GB", "CA", "AU", "IN", "ID", "BR", "MX", "ZA"]  # 注意：英国是GB而不是UK

    print(f"开始分析关键词 '{keyword}' 在 {len(country_list)} 个国家的市场需求...")
    print(f"使用并行处理和重试机制...")
    
    # 准备并行处理的参数
    args_list = [(keyword, country) for country in country_list]
    
    # 使用线程池并行处理
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # 限制最大并行数为3，避免API限制
        futures = {executor.submit(process_country, args): args for args in args_list}
        
        for future in concurrent.futures.as_completed(futures):
            args = futures[future]
            country = args[1]
            try:
                result = future.result()
                rows.append(result)
            except Exception as e:
                print(f"处理 {country} 时出现未捕获的错误: {e}")
                rows.append({
                    "country": country,
                    "population": 0,
                    "gdp_per_capita": 0,
                    "avg_cpc": 0,
                    "trend_slope": 0,
                    "pray_score": 0,
                    "error": str(e)
                })
    
    if not rows:
        print("没有成功获取任何国家的数据")
        exit(1)
        
    # 创建数据框并排序
    df = pd.DataFrame(rows).sort_values("pray_score", ascending=False)
    
    # 输出 CSV & 终端预览
    df.to_csv("pray_ranking.csv", index=False)
    print("\n最终结果:")
    print(df[["country", "pray_score", "population",
              "gdp_per_capita", "avg_cpc", "trend_slope"]])
    print(f"\n结果已保存到 pray_ranking.csv")