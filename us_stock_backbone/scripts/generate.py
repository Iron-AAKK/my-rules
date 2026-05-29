import os
from datetime import datetime

def main():
    # BASE_DIR: .../my-rules/us_stock_backbone/scripts
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RULE_ROOT = os.path.dirname(BASE_DIR)              # .../my-rules/us_stock_backbone
    REPO_ROOT = os.path.dirname(RULE_ROOT)             # .../my-rules
    DATA_DIR = os.path.join(RULE_ROOT, "data")         # .../my-rules/us_stock_backbone/data

    domains = set()
    keyword_rules = []  # 只给 .srs 用的 DOMAIN-KEYWORD 行

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

                upper = raw.upper()

                # 1) DOMAIN-KEYWORD 只保留给 .srs，不参与域名集合
                if upper.startswith("DOMAIN-KEYWORD"):
                    keyword_rules.append(raw)
                    continue

                # 2) 处理真正的域名
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

    # ---------- 1) my-rules/us_stock_backbone.list ----------
    # 对齐 futu.list / wenhua_cn.list：每行 +.domain，且不含 keyword
    list_path = os.path.join(REPO_ROOT, "us_stock_backbone.list")
    with open(list_path, "w", encoding="utf-8") as f:
        for d in sorted_domains:
            f.write(f"+.{d}\n")

    # ---------- 2) my-rules/us_stock_backbone.srs ----------
    # 先写 DOMAIN-KEYWORD 行，再写 DOMAIN-SUFFIX,domain
    srs_path = os.path.join(REPO_ROOT, "us_stock_backbone.srs")
    with open(srs_path, "w", encoding="utf-8") as f:
        for rule in keyword_rules:
            f.write(f"{rule}\n")
        for d in sorted_domains:
            f.write(f"DOMAIN-SUFFIX,{d}\n")

    # ---------- 3) my-rules/us_stock_backbone.yaml ----------
    # 对齐 wenhua_cn.yaml：payload: - .domain，不含 keyword
    yaml_path = os.path.join(REPO_ROOT, "us_stock_backbone.yaml")
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write("payload:\n")
        for d in sorted_domains:
            f.write(f"  - .{d}\n")

    # ---------- 4) README 只写在 my-rules/us_stock_backbone/ 目录 ----------
    readme_path = os.path.join(RULE_ROOT, "README.md")

    def get_kb(path: str) -> str:
        if not os.path.exists(path):
            return "0.0 KB"
        return f"{os.path.getsize(path) / 1024:.1f} KB"

    list_kb = get_kb(list_path)
    yaml_kb = get_kb(yaml_path)
    srs_kb = get_kb(srs_path)

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(
            f"# US Stock Backbone Rules\n\n"
            f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"## Statistics\n\n"
            f"- Total domains: **{len(sorted_domains)}**\n\n"
            f"## Files\n\n"
            f"- [us_stock_backbone.list](../us_stock_backbone.list)  ({list_kb})\n"
            f"- [us_stock_backbone.yaml](../us_stock_backbone.yaml)  ({yaml_kb})\n"
            f"- [us_stock_backbone.srs](../us_stock_backbone.srs)   ({srs_kb})\n\n"
            f"## Auto Update\n\n"
            f"This folder is automatically updated by GitHub Actions.\n"
        )

if __name__ == "__main__":
    main()
