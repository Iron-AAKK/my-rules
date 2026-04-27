import os
import re
import ssl
import socket
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# 当前脚本所在目录：huatai/scripts
BASE = os.path.dirname(os.path.abspath(__file__))

# 数据目录：huatai/data
DATA_DIR = os.path.join(BASE, "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

# -----------------------------
# 1. 基础域名（你提供的）
# -----------------------------
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

# -----------------------------
# 2. 官网 URL（你确认全部启用）
# -----------------------------
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

# -----------------------------
# 3. 垃圾域名过滤规则
# -----------------------------
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
    domain = domain.lower()
    return any(bad in domain for bad in BAD_KEYWORDS)


# -----------------------------
# 4. 提取域名
# -----------------------------
def extract_domains(text):
    if not text:
        return set()
    return set(re.findall(r"[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text))


# -----------------------------
# 5. 抓取 HTML 中的域名
# -----------------------------
def fetch_html_domains(url):
    try:
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        text = r.text

        # 提取所有链接
        links = set()
        for tag in soup.find_all(["a", "script", "img", "link"]):
            for attr in ["href", "src"]:
                if tag.has_attr(attr):
                    full = urljoin(url, tag[attr])
                    links |= extract_domains(full)

        # HTML 文本中的域名
        links |= extract_domains(text)

        return links
    except:
        return set()


# -----------------------------
# 6. 抓取 sitemap.xml
# -----------------------------
def fetch_sitemap(url):
    try:
        sitemap = url.rstrip("/") + "/sitemap.xml"
        r = requests.get(sitemap, timeout=5)
        if r.status_code != 200:
            return set()
        return extract_domains(r.text)
    except:
        return set()


# -----------------------------
# 7. 抓取 SSL SAN
# -----------------------------
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


# -----------------------------
# 8. 区域分类
# -----------------------------
def classify(domain):
    d = domain.lower()
    if d.endswith(".hk") or ".com.hk" in d:
        return "hk"
    if d.endswith(".sg") or ".com.sg" in d:
        return "sg"
    if "usa" in d or "-us" in d or d.endswith(".us"):
        return "us"
    return "cn"


# -----------------------------
# 9. 主流程
# -----------------------------
def main():
    results = {r: set(ROOT_DOMAINS[r]) for r in ROOT_DOMAINS}

    for region, urls in OFFICIAL_URLS.items():
        for url in urls:
            print(f"[{region}] Fetching HTML: {url}")
            results[region] |= fetch_html_domains(url)

            print(f"[{region}] Fetching sitemap: {url}")
            results[region] |= fetch_sitemap(url)

    # SSL 扫描（仅对基础域名）
    for region, roots in ROOT_DOMAINS.items():
        for root in roots:
            print(f"[{region}] Fetching SSL: {root}")
            results[region] |= fetch_ssl(root)

    # 过滤垃圾域名
    for region in results:
        clean = set()
        for d in results[region]:
            if not is_bad_domain(d):
                clean.add(d)
        results[region] = clean

    # 写入文件
    for region, domains in results.items():
        path = os.path.join(DATA_DIR, f"{region}-source.txt")
        with open(path, "w") as f:
            for d in sorted(domains):
                f.write(d + "\n")
        print(f"[{region}] {len(domains)} domains written → {path}")

    print("Done.")


if __name__ == "__main__":
    main()
