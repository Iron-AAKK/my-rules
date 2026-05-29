import asyncio
import aiohttp
import os
import time

API_URL = "https://api.certspotter.com/v1/issuances"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CertSpotterFetcher/1.0)"
}

async def fetch_certspotter(session, domain):
    params = {
        "domain": domain,
        "include_subdomains": "true",
        "expand": "dns_names"
    }

    print(f"\n[*] 扫描: {domain}")

    try:
        async with session.get(API_URL, params=params, headers=HEADERS) as resp:
            if resp.status == 429:
                print("[!] 429 Too Many Requests，等待 5 秒后重试")
                await asyncio.sleep(5)
                return await fetch_certspotter(session, domain)

            if resp.status != 200:
                print(f"[-] 非 200 响应: {resp.status}")
                return domain, []

            data = await resp.json()

            found = set()
            for item in data:
                for name in item.get("dns_names", []):
                    name = name.lower().replace("*.", "")
                    if name.endswith(domain):
                        found.add(name)

            print(f"[+] {domain} → 发现 {len(found)} 个子域名")
            await asyncio.sleep(1)
            return domain, sorted(found)

    except Exception as e:
        print(f"[-] 异常: {e}")
        return domain, []


async def main_async():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RULE_ROOT = os.path.dirname(BASE_DIR)
    DATA_DIR = os.path.join(RULE_ROOT, "data")

    BASE_FILE = os.path.join(DATA_DIR, "us_stock_backbone_base.txt")
    OUTPUT_FILE = os.path.join(DATA_DIR, "us_stock_backbone_discovered.txt")
    DIFF_FILE = os.path.join(DATA_DIR, "us_stock_backbone_diff.txt")

    # 读取域名
    with open(BASE_FILE, "r", encoding="utf-8") as f:
        domains = [l.strip() for l in f if l.strip() and not l.startswith("#")]

    print(f"[*] CertSpotter 扫描启动，共 {len(domains)} 个域名")

    async with aiohttp.ClientSession() as session:
        results = []
        for d in domains:
            r = await fetch_certspotter(session, d)
            results.append(r)

    # 汇总
    all_found = set()
    per_domain_stats = []

    for domain, subs in results:
        per_domain_stats.append((domain, len(subs)))
        all_found.update(subs)

    # 写入 discovered.txt
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(all_found)))

    print(f"\n[+] 扫描完成，共发现 {len(all_found)} 个唯一子域名。")

    # diff
    old_set = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            old_set = {l.strip() for l in f if l.strip()}

    diff = sorted(all_found - old_set)

    with open(DIFF_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(diff))

    print(f"[+] 新增域名 {len(diff)} 个（已写入 diff.txt）")

    # 统计
    print("\n========== 扫描统计报告 ==========")
    for d, count in per_domain_stats:
        print(f"{d:<30} → {count} 个子域名")
    print("=================================")


if __name__ == "__main__":
    asyncio.run(main_async())
