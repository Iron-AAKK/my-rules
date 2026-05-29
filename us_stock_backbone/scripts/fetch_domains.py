import requests
import os
import time

def fetch_subdomains_from_crt(domain, session):
    url = f"https://crt.sh/?q={domain}&output=json"
    for attempt in range(2):
        try:
            r = session.get(url, timeout=10)
            if r.status_code == 200 and "application/json" in r.headers.get("Content-Type", ""):
                # 使用 set 推导式直接返回精确匹配且去重的域名
                return {item['name_value'].lower().replace('*.', '') 
                        for item in r.json() 
                        if item['name_value'].lower().endswith(domain)}
        except Exception as e:
            print(f"[-] 异常: {domain} (尝试 {attempt+1}): {e}")
        time.sleep(1)
    return set()

def main():
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    BASE_FILE = os.path.join(DATA_DIR, "us_stock_backbone_base.txt")
    OUTPUT_FILE = os.path.join(DATA_DIR, "us_stock_backbone_discovered.txt")
    
    with open(BASE_FILE, "r") as f:
        targets = [l.strip() for l in f if l.strip() and not l.startswith("#")]

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; DomainScanner/1.0)"})
    
    all_found = set()
    print(f"[*] 共需扫描 {len(targets)} 个基础域名...")
    for t in targets:
        print(f"[*] Analyzing: {t}")
        all_found.update(fetch_subdomains_from_crt(t, session))
        time.sleep(0.3)
    
    with open(OUTPUT_FILE, "w") as f:
        f.write("\n".join(sorted(all_found)))
    print(f"[+] 扫描完成，共发现 {len(all_found)} 个域名。")

if __name__ == "__main__":
    main()
