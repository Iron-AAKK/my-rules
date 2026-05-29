import requests
import os
import json

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "..", "data")
    BASE_FILE = os.path.join(DATA_DIR, "us_stock_backbone_base.txt")
    OUTPUT_FILE = os.path.join(DATA_DIR, "us_stock_backbone_discovered.txt")
    
    if not os.path.exists(BASE_FILE): return

    with open(BASE_FILE, "r", encoding="utf-8") as f:
        targets = [l.strip() for l in f if l.strip() and not l.startswith("#")]

    session = requests.Session()
    all_found = set()
    
    print(f"[*] 开始扫描 {len(targets)} 个基础域名...")
    for target in targets:
        clean_target = target.replace("DOMAIN-SUFFIX,", "").replace("+.", "")
        url = f"https://crt.sh/?q={clean_target}&output=json"
        try:
            # 强制 10 秒超时
            r = session.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                for item in data:
                    name = item.get('name_value', '').lower()
                    if name.endswith(clean_target):
                        all_found.add(name.replace('*.', ''))
        except Exception:
            continue
            
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(all_found)))
    print(f"[+] 扫描结束，共发现 {len(all_found)} 个域名。")

if __name__ == "__main__":
    main()
