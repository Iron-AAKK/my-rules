import os
from datetime import datetime

# ==============================================================================
# 当前脚本所在目录: us_stock_backbone/scripts
# ==============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ==============================================================================
# 项目根目录: us_stock_backbone/
# ==============================================================================
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

# ==============================================================================
# 仓库根目录: my-rules/
# ==============================================================================
ROOT_DIR = os.path.dirname(PROJECT_DIR)

# ==============================================================================
# 数据源目录: us_stock_backbone/data/
# ==============================================================================
DATA_DIR = os.path.join(PROJECT_DIR, "data")

def main():
    # 定位输入源
    base_file_path = os.path.join(DATA_DIR, "us_stock_backbone_base.txt")
    
    if not os.path.exists(base_file_path):
        print(f"[-] 错误: 找不到底座文件 {base_file_path}")
        return

    # 读取并清洗数据
    domains = set()
    with open(base_file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 跳过空行和注释
            if not line or line.startswith("#"):
                continue
            # 兼容带有 '- ' 前缀的情况，提取核心规则
            if line.startswith("- "):
                line = line[2:].strip()
            domains.add(line)

    # 排序，保持规则集的整洁
    sorted_domains = sorted(list(domains))
    total_count = len(sorted_domains)
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --------------------------------------------------------------------------
    # 1. 生成仓库根目录下的 us_stock_backbone.yaml (Clash 订阅)
    # --------------------------------------------------------------------------
    yaml_output_path = os.path.join(ROOT_DIR, "us_stock_backbone.yaml")
    with open(yaml_output_path, "w", encoding="utf-8") as f:
        f.write(f"# Title: US Stock Backbone (Clash Payload)\n")
        f.write(f"# Total Count: {total_count}\n")
        f.write(f"# Last Updated: {update_time}\n")
        f.write("payload:\n")
        for domain in sorted_domains:
            f.write(f"  - '{domain}'\n")
    print(f"[+] 成功生成 Clash 规则集: {yaml_output_path} (数量: {total_count})")

    # --------------------------------------------------------------------------
    # 2. 生成仓库根目录下的 us_stock_backbone.list (OpenClash/Surge/PassWall)
    # --------------------------------------------------------------------------
    list_output_path = os.path.join(ROOT_DIR, "us_stock_backbone.list")
    with open(list_output_path, "w", encoding="utf-8") as f:
        f.write(f"# Title: US Stock Backbone (Universal List)\n")
        f.write(f"# Total Count: {total_count}\n")
        f.write(f"# Last Updated: {update_time}\n")
        for domain in sorted_domains:
            f.write(f"{domain}\n")
    print(f"[+] 成功生成通用规则集: {list_output_path} (数量: {total_count})")

    # --------------------------------------------------------------------------
    # 3. 自动更新子项目的 README.md 看板
    # --------------------------------------------------------------------------
    readme_path = os.path.join(PROJECT_DIR, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(f"# 美股交易基础设施核心骨干网 (US Stock Backbone)\n\n")
        f.write(f"本目录为独立项目模块，通过自动化脚本构建美股深水区清算、交易所及网络底层路由基建规则。\n\n")
        f.write(f"### 📊 规则构建状态看板\n\n")
        f.write(f"| 规则名称 | 订阅文件格式 | 包含域名总数 | 最后更新时间 |\n")
        f.write(f"| :--- | :--- | :--- | :--- |\n")
        f.write(f"| `us_stock_backbone.yaml` | Clash Payload | **{total_count}** | `{update_time}` |\n")
        f.write(f"| `us_stock_backbone.list` | OpenClash / Surge / PassWall | **{total_count}** | `{update_time}` |\n\n")
        f.write(f"### 🔗 软路由直接订阅链接\n\n")
        f.write(f"- **Clash 格式**: `https://raw.githubusercontent.com/{{{{ github.repository }}}}/main/us_stock_backbone.yaml`\n")
        f.write(f"- **通用 List 格式**: `https://raw.githubusercontent.com/{{{{ github.repository }}}}/main/us_stock_backbone.list`\n")
    print(f"[+] 成功更新自解释看板: {readme_path}")

if __name__ == "__main__":
    main()
