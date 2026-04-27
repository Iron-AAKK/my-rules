import os
import re
import ssl
import socket
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# ============================================================
# 当前脚本所在目录：wenhua/scripts
# ============================================================
BASE = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 数据目录：wenhua/data
# ============================================================
DATA_DIR = os.path.join(BASE, "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ============================================================
# 1. 文华财经基础域名（你提供的）
#    —— 这些域名永远保留，是整个系统的“根”
# ============================================================
ROOT_DOMAINS = {
    "cn": [
        # 核心品牌与官网
        "wenhua.com.cn",
        "wenhua.com",
        "wenhua.cn",
        "wenhua-tech.com",
        "wenhuacaijing.com",
        "shwenhua.com",

        # 文华 wh6/7/8/9 系列
        "wh6.cn",
        "wh6.com.cn",
        "wh7.cn",
        "wh7.com.cn",
        "wh8.cn",
        "wh8.com.cn",
        "wh9.cn",
        "wh9.com.cn",

        # 澎博财经 & 交易终端
        "pobo.cn",
        "pobo.net.cn",
        "pobofinance.com",
        "qh168.com",
        "qh168.com.cn",
    ]
}

# ============================================================
# 2. 文华财经官网 URL（用于抓取 HTML / sitemap）
# ============================================================
OFFICIAL_URLS = {
    "cn": [
        "https://www.wenhua.com.cn",
        "https://www.wenhua.com",
        "https://www.wenhua.cn",
        "https://www.wenhua-tech.com",
        "https://www.wenhuacaijing.com",
        "https://www.shwenhua.com",
    ]
}

# ============================================================
# 3. 垃圾域名过滤规则
# ============================================================
BAD_KEYWORDS = [
    "afternic",
    "wix",
    "domaincontrol",
    "dnsv5",
    "jomax",
    "outlook",
    "relaypod",
    "spf.",
    "root.cnolnic",
    "cloudflare",
    "akamai",
    "google",
    "gstatic",
    "doubleclick",
]

def is_bad_domain(domain):
    """判断是否为垃圾域名"""
    domain = domain.lower()
    return any(bad in domain for bad in BAD_KEYWORDS)

# ============================================================
# 4. 提取域名（正则）
# ============================================================
def extract_domains(text):
    if not text:
        return set()
    return set(re.findall(r"[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text))

# ============================================================
# 5. 抓取 HTML 中的域名
# ============================================================
def fetch_html_domains(url):
    try:
        r = requests.get(url, timeout=8)
        soup = BeautifulSoup(r.text, "html.parser")
        domains = set()

        # 提取所有链接
        for tag in soup.find_all(["a", "script", "img", "link"]):
            for attr in ["href", "src"]:
                if tag.has_attr(attr):
                    full = urljoin(url, tag[attr])
                    domains |= extract_domains(full)

        # HTML 文本中的域名
        domains |= extract_domains(r.text)

        return domains
    except:
        return set()

# ============================================================
# 6. 抓取 sitemap.xml
# ============================================================
def fetch_sitemap(url):
    try:
        sitemap = url.rstrip("/") + "/sitemap.xml"
        r = requests.get(sitemap, timeout=8)
        if r.status_code != 200:
            return set()
        return extract_domains(r.text)
    except:
        return set()

# ============================================================
# 7. 抓取 SSL SAN（证书中的域名）
# ============================================================
def fetch_ssl(domain):
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                san = cert.get("subjectAltName", [])
                return {d[1] for d in san if d[0] == "DNS"}
    except:
        return set()

# ============================================================
# 8. 判断域名是否属于根域名
# ============================================================
def is_under_root(domain, roots):
    d = domain.lower().strip(".")
    for root in roots:
        r = root.lower().strip(".")
        if d == r or d.endswith("." + r):
            return True
    return False

# ============================================================
# 9. 主流程
# ============================================================
def main():
    results = {"cn": set(ROOT_DOMAINS["cn"])}

    # -----------------------------
    # (1) 从官网 HTML / sitemap 抓取域名
    # -----------------------------
    for url in OFFICIAL_URLS["cn"]:
        print(f"[cn] HTML: {url}")
        html_domains = fetch_html_domains(url)

        print(f"[cn] sitemap: {url}")
        sitemap_domains = fetch_sitemap(url)

        for d in html_domains | sitemap_domains:
            if is_under_root(d, ROOT_DOMAINS["cn"]):
                results["cn"].add(d)

    # -----------------------------
    # (2) 从 SSL 证书中抓取 SAN
    # -----------------------------
    for root in ROOT_DOMAINS["cn"]:
        print(f"[cn] SSL: {root}")
        san_domains = fetch_ssl(root)

        for d in san_domains:
            if is_under_root(d, ROOT_DOMAINS["cn"]):
                results["cn"].add(d)

    # -----------------------------
    # (3) 过滤垃圾域名
    # -----------------------------
    clean = set()
    for d in results["cn"]:
        if not is_bad_domain(d):
            clean.add(d)
    results["cn"] = clean

    # -----------------------------
    # (4) 写入 wenhua/data/cn-source.txt
    # -----------------------------
    out = os.path.join(DATA_DIR, "cn-source.txt")
    with open(out, "w") as f:
        for d in sorted(results["cn"]):
            f.write(d + "\n")

    print(f"[cn] {len(results['cn'])} domains → {out}")
    print("Done.")

# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    main()
