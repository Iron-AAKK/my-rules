import aiohttp
import asyncio
import re
import os

SEARCH_URL = "https://duckduckgo.com/html/?q={query}"

# 你可以在这里添加更多关键词
KEYWORDS = [
    "nyse",
    "nasdaq",
    "cme",
    "cboe",
    "dtcc",
    "occ",
    "apex clearing",
    "drivewealth",
    "ibkr",
    "pershing",
    "plaid",
    "stripe",
    "visa",
    "mastercard",
    "sec",
    "finra",
    "treasury",
]

DOMAIN_REGEX = re.compile(r"https?://([A-Za-z0-9.-]+\.[A-Za-z]{2,})")

async def fetch_search(session, keyword):
    url = SEARCH_URL.format(query=keyword.replace(" ", "+"))
    print(f"\n[*] 搜索关键词: {keyword}")

    try:
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
            html = await resp.text()
            domains = set(re.findall(DOMAIN_REGEX, html))
            print(f"[+] {keyword} → 发现 {len(domains)} 个域名")
            return domains
    except Exception as e:
        print(f"[-] 异常: {e}")
        return set()

async def main_async():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT = os.path.dirname(BASE_DIR)
    DATA_DIR = os.path.join(ROOT, "data")

    OUTPUT_FILE = os.path.join(DATA_DIR, "us_stock_backbone_discovered.txt")
    DIFF_FILE = os.path.join(DATA_DIR, "us_stock_backbone_diff.txt")

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_search(session, kw) for kw in KEYWORDS]
        results = await asyncio.gather(*tasks)

    all_found = set()
    for r in results:
        all_found.update(r)

    # 写入 discovered.txt
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(all_found)))

    print(f"\n[+] 总共发现 {len(all_found)} 个唯一域名")

    # diff
    old_set = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            old_set = {l.strip() for l in f if l.strip()}

    diff = sorted(all_found - old_set)

    with open(DIFF_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(diff))

    print(f"[+] 新增域名 {len(diff)} 个（已写入 diff.txt）")

if __name__ == "__main__":
    asyncio.run(main_async())
