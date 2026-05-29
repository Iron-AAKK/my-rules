import requests
import json
import os

# 定义你的“骨干网核心关键词”
# 只有包含这些关键词的子域名才会被录入，过滤掉垃圾数据
KEYWORDS = ['api', 'quote', 'stock', 'trade', 'data', 'web', 'connect']

def fetch_subdomains_from_crt(domain):
    url = f"https://crt.sh/?q={domain}&output=json"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            return []
        
        data = response.json()
        subdomains = set()
        
        for entry in data:
            name = entry.get("name_value", "").lower()
            # 过滤逻辑：
            # 1. 必须以目标域名结尾
            # 2. 必须包含定义的关键词之一
            if name.endswith(domain) and any(kw in name for kw in KEYWORDS):
                subdomains.add(name)
        
        return list(subdomains)
    except Exception as e:
        print(f"[-] 扫描出错 {domain}: {e}")
        return []

def main():
    # 根目录路径
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
    DATA_DIR = os.path.join(PROJECT_DIR, "data")
    OUTPUT_FILE = os.path.join(DATA_DIR, "us_stock_backbone_discovered.txt")
    BASE_FILE = os.path.join(DATA_DIR, "us_stock_backbone_base.txt")

    # 读取底座中的目标域名进行扫描
    if not os.path.exists(BASE_FILE):
        return

    targets = []
    with open(BASE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 简单提取域名主体
            if line and not line.startswith("#"):
                clean = line.replace("DOMAIN-SUFFIX,", "").replace("+.", "")
                targets.append(clean)

    all_discovered = set()
    for target in targets:
        print(f"[*] 正在扫描: {target}")
        found = fetch_subdomains_from_crt(target)
        all_discovered.update(found)

    # 写入发现的结果
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for domain in sorted(list(all_discovered)):
            f.write(f"{domain}\n")
    
    print(f"[+] 扫描完成，共发现 {len(all_discovered)} 个核心骨干域名。")

if __name__ == "__main__":
    main()
