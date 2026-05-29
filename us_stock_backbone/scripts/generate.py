import os
from datetime import datetime

# ==============================================================================
# 路径解析 (完全对齐你的动态路径标准)
# ==============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
ROOT_DIR = os.path.dirname(PROJECT_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, "data")

def main():
    domains = set()

    # --------------------------------------------------------------------------
    # 输入源 1：读取手写核心底座文件
    # --------------------------------------------------------------------------
    base_file_path = os.path.join(DATA_DIR, "us_stock_backbone_base.txt")
    if os.path.exists(base_file_path):
        with open(base_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("- "):
                    line = line[2:].strip()
                domains.add(line)
        print(f"[+] 成功加载核心底座数据: {base_file_path}")
    else:
        print(f"[-] 警告: 找不到底座文件 {base_file_path}")

    # --------------------------------------------------------------------------
    # 输入源 2：自适应读取雷达自动抓取的新域名库 (存在则合并，不存在则优雅跳过)
    # --------------------------------------------------------------------------
    discovered_file_path = os.path.join(DATA_DIR, "us_stock_backbone_discovered.txt")
    if os.path.exists(discovered_file_path):
        with open(discovered_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("- "):
                    line = line[2:].strip()
                domains.add(line)
        print(f"[+] 成功联合合并雷达扫描数据: {discovered_file_path}")
    else:
        print(f"[i] 提示: 尚未生成雷达动态数据，本次仅编译底座。")

    if not domains:
        print("[-] 错误: 规则集内容为空，取消编译输出。")
        return

    # --------------------------------------------------------------------------
    # 统一清洗、去重与字典序排序
    # --------------------------------------------------------------------------
    sorted_domains = sorted(list(domains))
    total_count = len(sorted_domains)
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --------------------------------------------------------------------------
    # 成果 1: 编译输出至仓库根目录下的 us_stock_backbone.yaml (Clash)
    # --------------------------------------------------------------------------
    yaml_output_path = os.path.join(ROOT_DIR, "us_stock_backbone.yaml")
    with open(yaml_output_path, "w", encoding="utf-8") as f:
        f.write(f"# Title: US Stock Backbone (Clash Payload)\n")
        f.write(f"# Total Count: {total_count}\n")
        f.write(f"# Last Updated: {update_time}\n")
        f.write("payload:\n")
        for domain in sorted_domains:
            f.write(f"  - '{domain}'\n")
    print(f"[+] 成果已甩至根目录 Clash 规则: {yaml_output_path} (数量: {total_count})")

    # --------------------------------------------------------------------------
    # 成果 2: 编译输出至仓库根目录下的 us_stock_backbone.list (通用)
    # --------------------------------------------------------------------------
    list_output_path = os.path.join(ROOT_DIR, "us_stock_backbone.list")
    with open(list_output_path, "w", encoding="utf-8") as f:
        f.write(f"# Title: US Stock Backbone (Universal List)\n")
        f.write(f"# Total Count: {total_count}\n")
        f.write(f"# Last Updated: {update_time}\n")
        for domain in sorted_domains:
            f.write(f"{domain}\n")
    print(f"[+] 成果已甩至根目录通用 List 规则: {list_output_path} (数量: {total_count})")

    # --------------------------------------------------------------------------
    # 成果 3: 自动刷新本项目主页的 README.md 看板
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
    print(f"[+] 看板自动同步刷新完成: {readme_path}")

if __name__ == "__main__":
    main()
