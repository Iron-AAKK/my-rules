import os
from datetime import datetime

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))          # .../my-rules/us_stock_backbone/scripts
    RULE_ROOT = os.path.dirname(BASE_DIR)                          # .../my-rules/us_stock_backbone
    REPO_ROOT = os.path.dirname(RULE_ROOT)                         # .../my-rules
    DATA_DIR = os.path.join(RULE_ROOT, "data")                     # .../my-rules/us_stock_backbone/data

    domains = set()
    keyword_rules = []  # 只给 .srs 用

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

                # ---------- 关键：keyword 只进 .srs ----------
                if upper.startswith("DOMAIN-KEYWORD"):
                    keyword_rules.append(raw)
                    continue

                # ---------- 过滤掉 DOMAIN-SUFFIX,domain ----------
                if upper.startswith("DOMAIN-SUFFIX,"):
                    raw = raw.split(",", 1)[1].strip()

                # ---------- 清洗域名 ----------
                d = (
                    raw.replace("+.", "")
                       .lstrip(".")
                       .strip()
                )

                # ---------- 再次过滤 keyword 残留 ----------
                if d.upper().startswith("DOMAIN-KEYWORD"):
                    continue

                if d:
                    domains.add(d)

    if len(domains) < 5:
        raise ValueError(f"[!] 域名数量异常 ({len(domains)})，停止生成。")

    sorted_domains = sorted(domains)

    # ---------- 1) us_stock_backbone.list ----------
    list_path = os.path.join(REPO_ROOT, "us_stock_backbone.list")
    with open(list_path, "w", encoding="utf-8") as f:
        for d in sorted_domains:
            f.write(f"+.{d}\n")

    # ---------- 2) us_stock_backbone.yaml ----------
    yaml_path = os.path.join(REPO_ROOT, "us_stock_backbone.yaml")
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write("payload:\n")
        for d in sorted_domains:
            f.write(f"  - +.{d}\n")

    # ---------- 3) us_stock_backbone.srs ----------
    srs_path = os.path.join(REPO_ROOT, "us_stock_backbone.srs")
    with open(srs_path, "w", encoding="utf-8") as f:
        for rule in keyword_rules:
            f.write(f"{rule}\n")
        for d in sorted_domains:
            f.write(f"DOMAIN-SUFFIX,{d}\n")

    # ---------- 4) README（只写在 us_stock_backbone/） ----------
    readme_path = os.path.join(RULE_ROOT, "README.md")

    def get_kb(path: str) -> str:
        if not os.path.exists(path):
            return "0.0 KB"
        return f"{os.path.getsize(path) / 1024:.1f} KB"

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(
            f"# US Stock Backbone Rules\n\n"
            f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"## Statistics\n\n"
            f"- Total domains: **{len(sorted_domains)}**\n\n"
            f"## Files\n\n"
            f"- [us_stock_backbone.list](../us_stock_backbone.list)  ({get_kb(list_path)})\n"
            f"- [us_stock_backbone.yaml](../us_stock_backbone.yaml)  ({get_kb(yaml_path)})\n"
            f"- [us_stock_backbone.srs](../us_stock_backbone.srs)   ({get_kb(srs_path)})\n\n"
            f"## Auto Update\n\n"
            f"This folder is automatically updated by GitHub Actions.\n"
        )

if __name__ == "__main__":
    main()
