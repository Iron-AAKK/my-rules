import os
import re
import requests
from datetime import datetime

# ==============================================================================
# 路径解析 (完全对齐你的动态路径标准)
# ==============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, "data")

# ==============================================================================
# 雷达扫描核心目标群 (针对根域名进行全子域名穿透扫描)
# ==============================================================================
TARGET_ROOTS = [
    "nyse.com",
    "nasdaq.com",
    "apexclearing.com",
    "drivewealth.com",
    "cboe.com",
    "cmegroup.com",
    "plaid.com"
]

def fetch_subdomains_from_crt(domain):
    """通过 crt.sh 证书日志网关，扫描捕获该域名旗下所有隐藏的子域名"""
    print(f"[+] 雷达正在扫描探测: {domain} ...")
    url = f"https://crt.sh/?q=%.{domain}&output=json"
    subdomains = set()
    try:
        # 设置15秒超时，防止网络死锁
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            for item in data:
                # 提取证书中的常用名(Common Name)或匹配名
                name = item.get("name_value", "").lower()
                # 可能会有通配符或多域名换行，进行清洗
                names = name.split("\n")
                for n in names:
                    n = n.strip()
                    if n.startswith("*."):
                        n = n[2:]
                    # 确保抓到的是合法的、属于该目标的域名
                    if n and n.endswith(domain) and re.match(r'^[a-z0-9.-]+$', n):
                        subdomains.add(n)
        print(f"[v] {domain} 扫描完毕，捕获到 {len(subdomains)} 个活跃域名")
    except Exception as e:
        print(f"[-] 警告: {domain} 雷达扫描超时或失败 (原因: {e})")
    return subdomains

def main():
    all_discovered_domains = set()

    # 1. 启动雷达，遍历扫荡所有核心目标
    for root in TARGET_ROOTS:
        discovered = fetch_subdomains_from_crt(root)
        all_discovered_domains.update(discovered)

    if not all_discovered_domains:
        print("[-] 本次雷达扫描未发现新数据，终止写入。")
        return

    # 2. 转换成标准的规则格式 (DOMAIN-SUFFIX 或 DOMAIN)
    formatted_rules = set()
    for domain in all_discovered_domains:
        # 如果是核心根域名本身，走 SUFFIX 拦截全网
        if domain in TARGET_ROOTS:
            formatted_rules.add(f"- DOMAIN-SUFFIX,{domain}")
        else:
            # 精确检测到的子域名，用 DOMAIN 精准直连，防止大范围误杀
            formatted_rules.add(f"- DOMAIN,{domain}")

    # 3. 定位自动存储路径，写入 us_stock_backbone_discovered.txt
    output_file = os.path.join(DATA_DIR, "us_stock_backbone_discovered.txt")
    
    # 排序并写入
    sorted_rules = sorted(list(formatted_rules))
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# ==========================================================\n")
        f.write(f"# 🔴 雷达自动捕获的美股高频基建动态域名库\n")
        f.write(f"# 最后扫描更新时间: {update_time}\n")
        f.write(f"# 数量: {len(sorted_rules)}\n")
        f.write(f"# ==========================================================\n")
        for rule in sorted_rules:
            f.write(f"{rule}\n")

    print(f"[+] 雷达扫描数据已完美归盘: {output_file} (总计: {len(sorted_rules)} 条规则)")

if __name__ == "__main__":
    main()
