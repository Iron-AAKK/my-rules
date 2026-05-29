import os
from datetime import datetime

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
    DATA_DIR = os.path.join(BASE_DIR, "..", "data")
    
    domains = set()
    for f_name in ["us_stock_backbone_base.txt", "us_stock_backbone_discovered.txt"]:
        path = os.path.join(DATA_DIR, f_name)
        if os.path.exists(path):
            with open(path, "r") as f:
                for line in f:
                    d = line.strip().replace("DOMAIN-SUFFIX,", "").replace("+.", "").replace("DOMAIN,", "")
                    if d: domains.add(d)

    if len(domains) < 5:
        raise ValueError(f"[!] 异常：发现域名数量过少 ({len(domains)})，停止生成以防误操作。")

    sorted_domains = sorted(list(domains))
    
    # 写入 YAML (美观换行)
    with open(os.path.join(ROOT_DIR, "us_stock_backbone.yaml"), "w") as f:
        f.write("payload:\n")
        for d in sorted_domains:
            f.write(f"  - +.{d}\n")
    
    # 写入其余格式
    with open(os.path.join(ROOT_DIR, "us_stock_backbone.list"), "w") as f:
        f.write("\n".join([f"+.{d}" for d in sorted_domains]))
    with open(os.path.join(ROOT_DIR, "us_stock_backbone.srs"), "w") as f:
        f.write("\n".join([f"DOMAIN-SUFFIX,{d}" for d in sorted_domains]))

    def get_kb(name): return f"{os.path.getsize(os.path.join(ROOT_DIR, name))/1024:.1f} KB"

    with open(os.path.join(ROOT_DIR, "README.md"), "w") as f:
        f.write(f"# US Stock Backbone Rules\n\nUpdated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"### 统计信息\n- 总域名数: {len(sorted_domains)}\n\n"
                f"### 文件大小\n- list: {get_kb('us_stock_backbone.list')}\n- yaml: {get_kb('us_stock_backbone.yaml')}\n- srs: {get_kb('us_stock_backbone.srs')}\n\n"
                f"### 规则列表\n- [us_stock_backbone.list](./us_stock_backbone.list)\n- [us_stock_backbone.yaml](./us_stock_backbone.yaml)\n- [us_stock_backbone.srs](./us_stock_backbone.srs)")

if __name__ == "__main__":
    main()
