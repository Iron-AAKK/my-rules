import os
from datetime import datetime

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))          # .../us_stock_backbone/scripts
    ROOT_DIR = os.path.dirname(BASE_DIR)                           # .../us_stock_backbone
    DATA_DIR = os.path.join(ROOT_DIR, "data")

    domains = set()

    for f_name in ["us_stock_backbone_base.txt", "us_stock_backbone_discovered.txt"]:
        path = os.path.join(DATA_DIR, f_name)
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                raw = line.strip()
                if not raw:
                    continue
                if raw.startswith("#"):
                    continue
                if raw.upper().startswith("DOMAIN-KEYWORD"):
                    continue

                d = (
                    raw.replace("DOMAIN-SUFFIX,", "")
                       .replace("DOMAIN,", "")
                       .replace("+.", "")
                       .lstrip(".")
                       .strip()
                )
                if d:
                    domains.add(d)

    if len(domains) < 5:
        raise ValueError(f"[!] 安全警告：生成的域名数量 ({len(domains)}) 过低，终止操作以保护数据完整性。")

    sorted_domains = sorted(domains)

    # 1) us_stock_backbone.list  —— 参考 wenhua_cn.list：每行 +.domain
    list_path = os.path.join(ROOT_DIR, "us_stock_backbone.list")
    with open(list_path, "w", encoding="utf-8") as f:
        for d in sorted_domains:
            f.write(f"+.{d}\n")

    # 2) us_stock_backbone.srs  —— 参考 wenhua_cn.srs：每行 DOMAIN-SUFFIX,domain
    srs_path = os.path.join(ROOT_DIR, "us_stock_backbone.srs")
    with open(srs_path, "w", encoding="utf-8") as f:
        for d in sorted_domains:
            f.write(f"DOMAIN-SUFFIX,{d}\n")

    # 3) us_stock_backbone.yaml —— 参考 wenhua_cn.yaml：payload: - .domain
    yaml_path = os.path.join(ROOT_DIR, "us_stock_backbone.yaml")
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write("payload:\n")
        for d in sorted_domains:
            f.write(f"  - .{d}\n")

    # README：放在 us_stock_backbone/ 目录下，去掉 badge 和写死的 258
    readme_path = os.path.join(ROOT_DIR, "README.md")

    def get_kb(name: str) -> str:
        full = os.path.join(ROOT_DIR, name)
        if not os.path.exists(full):
            return "0.0 KB"
        return f"{os.path.getsize(full) / 1024:.1f} KB"

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(
            f"# US Stock Backbone Rules\n\n"
            f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"## Statistics\n\n"
            f"- Total domains: **{len(sorted_domains)}**\n\n"
            f"## Files\n\n"
            f"- [us_stock_backbone.list](./us_stock_backbone.list)  ({get_kb('us_stock_backbone.list')})\n"
            f"- [us_stock_backbone.yaml](./us_stock_backbone.yaml)  ({get_kb('us_stock_backbone.yaml')})\n"
            f"- [us_stock_backbone.srs](./us_stock_backbone.srs)   ({get_kb('us_stock_backbone.srs')})\n\n"
            f"## Auto Update\n\n"
            f"This folder is automatically updated by GitHub Actions.\n"
        )

if __name__ == "__main__":
    main()
