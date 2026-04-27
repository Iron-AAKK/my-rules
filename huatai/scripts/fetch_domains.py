import os
import re
import ssl
import socket
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# ============================================================
# 当前脚本所在目录：huatai/scripts
# ============================================================
BASE = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 数据目录：huatai/data
# ============================================================
DATA_DIR = os.path.join(BASE, "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ============================================================
# 1. 基础域名（你提供的）
#    —— 这些域名永远保留，是整个系统的“根”
# ============================================================
ROOT_DOMAINS = {
    "cn": [
        "htsc.com.cn",
        "htsc.com",
        "htsc.cn",
        "95597.com",
        "htsc-api.com",
        "htsham.com",
        "htiam.com",
        "htf.com",
        "chinatai.com",
        "chinatai.com.cn",
        "htzq.cn",
        "static.htsc.com.cn",
        "api.htsc.com.cn",
        "cdn.htsc.com.cn",
        "img.htsc.com.cn",
        "htsc.net",
        "htsc.org",
        "htsc.co",
        "htsc.info",
        "htsc.biz",
        "htsec.com",
        "htsec.cn",
        "htsec.com.cn",
    ],

    "hk": [
        "htsc.com.hk",
        "htsc.hk",
        "htisec.com",
        "htisec.hk",
        "htihk.com",
        "htintl.com",
        "zhangle-global.com",
        "htsc-service.com",
        "www.htisec.com.hk",
        "api.htisec.com",
        "cdn.htisec.com",
    ],

    "us": [
        "htsc-us.com",
        "htsc-usa.com",
        "htamusa.com",
        "htscusa.com",
        "api.htsc-us.com",
        "api.htscusa.com",
        "static.htscusa.com",
    ],

    "sg": [
        "htsc.com.sg",
        "htsc.sg",
        "htisg.com",
        "htisec.com.sg",
        "htsc-sg.com",
    ],
}

# ============================================================
# 2. 官网 URL（你确认全部启用）
#    —— 只从这些官网页面提取域名
# ============================================================
OFFICIAL_URLS = {
    "cn": [
        "https://www.htsc.com.cn",
        "https://www.htsc.com",
        "https://www.htsc.cn",
        "https://www.chinatai.com",
        "https://www.chinatai.com.cn",
    ],
    "hk": [
        "https://www.htsc.com.hk",
        "https://www.htisec.com",
        "https://www.htisec.hk",
    ],
    "us": [
        "https://www.htsc-us.com",
        "https://www.htscusa.com",
    ],
    "sg": [
        "https://www.htsc.com.sg",
        "https://www.htisg.com",
    ],
}

# ============================================================
# 3. 垃圾域名过滤规则
#    —— 这些域名绝对不是华泰业务域名
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
# 8. 判断域名是否属于某区域的根域名
#    —— 只保留“根域名”或“根域名的子域名”
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
    # 初始化：每个区域先放入基础域名
    results = {r: set(ROOT_DOMAINS[r]) for r in ROOT_DOMAINS}

    # -----------------------------
    # (1) 从官网 HTML / sitemap 抓取域名
    # -----------------------------
    for region, urls in OFFICIAL_URLS.items():
        roots = ROOT_DOMAINS[region]

        for url in urls:
            print(f"[{region}] HTML: {url}")
            html_domains = fetch_html_domains(url)

            print(f"[{region}] sitemap: {url}")
            sitemap_domains = fetch_sitemap(url)

            # 只保留属于根域名的域名
            for d in html_domains | sitemap_domains:
                if is_under_root(d, roots):
                    results[region].add(d)

    # -----------------------------
    # (2) 从基础域名的 SSL 证书中抓取 SAN
    # -----------------------------
    for region, roots in ROOT_DOMAINS.items():
        for root in roots:
            print(f"[{region}] SSL: {root}")
            san_domains = fetch_ssl(root)

            for d in san_domains:
                if is_under_root(d, roots):
                    results[region].add(d)

    # -----------------------------
    # (3) 过滤垃圾域名
    # -----------------------------
    for region in results:
        clean = set()
        for d in results[region]:
            if not is_bad_domain(d):
                clean.add(d)
        results[region] = clean

    # -----------------------------
    # (4) 写入 huatai/data/{region}-source.txt
    # -----------------------------
    for region, domains in results.items():
        path = os.path.join(DATA_DIR, f"{region}-source.txt")
        with open(path, "w") as f:
            for d in sorted(domains):
                f.write(d + "\n")

        print(f"[{region}] {len(domains)} domains → {path}")

    print("Done.")

# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    main()
