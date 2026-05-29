import asyncio
import aiohttp
import async_timeout
import os

CONCURRENCY = 10
RETRIES = 3
CONNECT_TIMEOUT = 5
READ_TIMEOUT = 5

SEM = asyncio.Semaphore(CONCURRENCY)

async def fetch_json(session, url):
    """带超时、重试、限流保护的 JSON 请求"""
    for attempt in range(1, RETRIES + 1):
        try:
            async with SEM:
                with async_timeout.timeout(CONNECT_TIMEOUT + READ_TIMEOUT):
                    async with session.get(url) as resp:
                        if resp.status == 429:
                            print("[!] 429 Too Many Requests，等待 3 秒后重试")
                            await asyncio.sleep(3)
                            continue

                        if resp.status != 200:
                            print(f"[-] 非 200 响应: {resp.status}")
                            return None

                        if "application/json" not in resp.headers.get("Content-Type", ""):
                            print("[-] 非 JSON 响应（可能被限流）")
                            return None

                        return await resp.json()

        except asyncio.TimeoutError:
            print(f"[-] 请求超时（尝试 {attempt}/{RETRIES}）")
        except Exception as e:
            print(f"[-] 异常: {e}")

        await asyncio.sleep(1)

    return None


async def fetch_domain(session, domain):
    """扫描单个域名"""
    url = f"https://crt.sh/?q={domain}&output=json"
    print(f"[*] 扫描: {domain}")

    data = await fetch_json(session, url)
    if not data:
        return []

    results = set()
    for item in data:
        name = item.get("name_value", "").lower().replace("*.", "")
        if name.endswith(domain):
            results.add(name)

    return results


async def main_async():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.dirname(BASE_DIR)
    DATA_DIR = os.path.join(ROOT_DIR, "data")
    BASE_FILE = os.path.join(DATA_DIR, "us_stock_backbone_base.txt")
    OUTPUT_FILE = os.path.join(DATA_DIR, "us_stock_backbone_discovered.txt")

    with open(BASE_FILE, "r") as f:
        targets = [l.strip() for l in f if l.strip() and not l.startswith("#")]

    print(f"[*] 异步扫描启动，共 {len(targets)} 个域名")

    connector = aiohttp.TCPConnector(limit=50, ssl=False)
    timeout = aiohttp.ClientTimeout(
        total=None,
        connect=CONNECT_TIMEOUT,
        sock_read=READ_TIMEOUT
    )

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [fetch_domain(session, t) for t in targets]
        results = await asyncio.gather(*tasks)

    all_found = set()
    for r in results:
        all_found.update(r)

    with open(OUTPUT_FILE, "w") as f:
        f.write("\n".join(sorted(all_found)))

    print(f"[+] 扫描完成，共发现 {len(all_found)} 个域名。")


if __name__ == "__main__":
    asyncio.run(main_async())
