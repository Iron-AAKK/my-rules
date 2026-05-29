import asyncio
import aiohttp
import async_timeout
import os

# ========== 限流参数（方案 1） ==========
CONCURRENCY = 1          # 并发从 10 → 1
RETRIES = 3
CONNECT_TIMEOUT = 10     # crt.sh 很慢，适当加长
READ_TIMEOUT = 10
REQUEST_DELAY = 2        # 每次请求后 sleep 2 秒
DOMAIN_DELAY = 1         # 每个域名之间再 sleep 1 秒

SEM = asyncio.Semaphore(CONCURRENCY)


def clean_domain(line: str):
    """
    清洗 base.txt 的每一行：
    - 去掉前缀符号（-、空格）
    - 去掉 DOMAIN-SUFFIX, DOMAIN, DOMAIN-KEYWORD
    - 去掉注释
    - 返回纯域名
    """
    line = line.strip()

    if not line or line.startswith("#"):
        return None

    # 去掉前缀符号
    while line and line[0] in "-+ ":
        line = line[1:].lstrip()

    # 去掉 DOMAIN-SUFFIX, DOMAIN, DOMAIN-KEYWORD
    if "," in line:
        parts = line.split(",", 1)
        line = parts[1].strip()

    if "KEYWORD" in line.upper():
        return None

    if "." not in line:
        return None

    return line


async def fetch_json(session, url):
    for attempt in range(1, RETRIES + 1):
        try:
            async with SEM:
                with async_timeout.timeout(CONNECT_TIMEOUT + READ_TIMEOUT):
                    async with session.get(url) as resp:

                        # 限流处理
                        if resp.status == 429:
                            print("[!] 429 Too Many Requests，等待 5 秒后重试")
                            await asyncio.sleep(5)
                            continue

                        if resp.status != 200:
                            print(f"[-] 非 200 响应: {resp.status}")
                            return None

                        if "application/json" not in resp.headers.get("Content-Type", ""):
                            print("[-] 非 JSON 响应（可能被限流）")
                            return None

                        data = await resp.json()

                        # 每次请求后强制延迟
                        await asyncio.sleep(REQUEST_DELAY)

                        return data

        except asyncio.TimeoutError:
            print(f"[-] 请求超时（尝试 {attempt}/{RETRIES}）")
        except Exception as e:
            print(f"[-] 异常: {e}")

        await asyncio.sleep(1)

    return None


async def fetch_domain(session, domain):
    url = f"https://crt.sh/?q={domain}&output=json"
    print(f"\n[*] 扫描: {domain}")

    data = await fetch_json(session, url)
    if not data:
        print(f"[!] {domain} 扫描失败（无数据）")
        return domain, []

    results = set()
    for item in data:
        name = item.get("name_value", "").lower().replace("*.", "")
        if name.endswith(domain):
            results.add(name)

    print(f"[+] {domain} → 发现 {len(results)} 个子域名")

    # 每个域名之间再延迟
    await asyncio.sleep(DOMAIN_DELAY)

    return domain, sorted(results)


async def main_async():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RULE_ROOT = os.path.dirname(BASE_DIR)
    DATA_DIR = os.path.join(RULE_ROOT, "data")

    BASE_FILE = os.path.join(DATA_DIR, "us_stock_backbone_base.txt")
    OUTPUT_FILE = os.path.join(DATA_DIR, "us_stock_backbone_discovered.txt")
    DIFF_FILE = os.path.join(DATA_DIR, "us_stock_backbone_diff.txt")

    # 读取并清洗基础域名
    targets = []
    with open(BASE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            d = clean_domain(line)
            if d:
                targets.append(d)

    print(f"[*] 异步扫描启动，共 {len(targets)} 个基础域名")

    connector = aiohttp.TCPConnector(limit=10, ssl=False)
    timeout = aiohttp.ClientTimeout(
        total=None,
        connect=CONNECT_TIMEOUT,
        sock_read=READ_TIMEOUT
    )

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        results = []
        for t in targets:
            r = await fetch_domain(session, t)
            results.append(r)

    # 汇总所有发现的域名
    all_found = set()
    per_domain_stats = []

    for domain, subs in results:
        per_domain_stats.append((domain, len(subs)))
        all_found.update(subs)

    # 写入 discovered.txt
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(all_found)))

    print(f"\n[+] 扫描完成，共发现 {len(all_found)} 个唯一子域名。")

    # Diff 对比（新增域名）
    old_set = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            old_set = {l.strip() for l in f if l.strip()}

    new_set = all_found
    diff = sorted(new_set - old_set)

    with open(DIFF_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(diff))

    print(f"[+] 新增域名 {len(diff)} 个（已写入 diff.txt）")

    # 打印扫描统计报告
    print("\n========== 扫描统计报告 ==========")
    for d, count in per_domain_stats:
        print(f"{d:<30} → {count} 个子域名")
    print("=================================")


if __name__ == "__main__":
    asyncio.run(main_async())
