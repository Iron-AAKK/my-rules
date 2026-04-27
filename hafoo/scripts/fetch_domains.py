import os
import re
import ssl
import socket
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# ============================================================
# 当前脚本所在目录：hafoo/scripts
# ============================================================
BASE = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 数据目录：hafoo/data
# ============================================================
DATA_DIR = os.path.join(BASE, "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ============================================================
# 1. Hafoo（哈富证券）基础域名（你提供的）
#    —— 这些域名永远保留，是整个系统的“根”
# ============================================================
ROOT_DOMAINS = {
    "hk": [
        # 哈富核心品牌（核心业务流）
        "hafoo.com.hk",
        "hafoo.com",
        "hafoosec.com",

        # 东方财富最小子集（鉴权 / 验证码 / 基础数据）
        "dfcfw.com",
        "eastmoney.com",
        "1234567.com.cn",
    ]
}

# ============================================================
# 2. Hafoo 官网 URL（用于抓取 HTML / sitemap）
# ============================================================
OFFICIAL_URLS = {
    "hk": [
        "https://www.hafoo.com.hk",
        "https://www.hafoo.com.hk/cn/hans/about",
        "https://www.hafoo.com",
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
    results = {"hk": set(ROOT_DOMAINS["hk"])}

    # -----------------------------
    # (1) 从官网 HTML / sitemap 抓取域名
    # -----------------------------
    for url in OFFICIAL_URLS["hk"]:
        print(f"[hk] HTML: {url}")
        html_domains = fetch_html_domains(url)

        print(f"[hk] sitemap: {url}")
        sitemap_domains = fetch_sitemap(url)

        for d in html_domains | sitemap_domains:
            if is_under_root(d, ROOT_DOMAINS["hk"]):
                results["hk"].add(d)

    # -----------------------------
    # (2) 从 SSL 证书中抓取 SAN
    # -----------------------------
    for root in ROOT_DOMAINS["hk"]:
        print(f"[hk] SSL: {root}")
        san_domains = fetch_ssl(root)

        for d in san_domains:
            if is_under_root(d, ROOT_DOMAINS["hk"]):
                results["hk"].add(d)

    # -----------------------------
    # (3) 修复：过滤 *.domain.com / .*.domain.com
    # -----------------------------
    fixed = set()
    for d in results["hk"]:
        d = d.lstrip("*.")   # 去掉 "*." 或 ".*."
        d = d.lstrip(".")    # 避免出现 ".domain.com"
        fixed.add(d)

    results["hk"] = fixed

    # -----------------------------
    # (4) 过滤垃圾域名
    # -----------------------------
    clean = set()
    for d in results["hk"]:
        if not is_bad_domain(d):
            clean.add(d)
    results["hk"] = clean

    # -----------------------------
    # (5) 写入 hafoo/data/hk-source.txt
    # -----------------------------
    out = os.path.join(DATA_DIR, "hk-source.txt")
    with open(out, "w") as f:
        for d in sorted(results["hk"]):
            f.write(d + "\n")

    print(f"[hk] {len(results['hk'])} domains → {out}")
    print("Done.")

# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    main()
