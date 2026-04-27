import subprocess
import ssl
import socket
import re
import requests
import xml.etree.ElementTree as ET
import os

# 当前脚本所在目录：huatai/scripts
BASE = os.path.dirname(os.path.abspath(__file__))

# 数据目录：huatai/data
DATA_DIR = os.path.join(BASE, "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

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

        # 深度扫描新增（高概率）
        "static.htsc.com.cn",
        "api.htsc.com.cn",
        "cdn.htsc.com.cn",
        "img.htsc.com.cn",

        # 品牌保护域名
        "htsc.net",
        "htsc.org",
        "htsc.co",
        "htsc.info",
        "htsc.biz",

        # 历史遗留域名
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

        # 深度扫描新增
        "www.htisec.com.hk",
        "api.htisec.com",
        "cdn.htisec.com",
    ],

    "us": [
        "htsc-us.com",
        "htsc-usa.com",
        "htamusa.com",
        "htscusa.com",

        # 深度扫描新增
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


def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True)
    except Exception:
        return ""


def extract_domains(text):
    if not text:
        return set()
    return set(re.findall(r"[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text))


def fetch_dns(domain):
    output = run(f"dig {domain} ANY +short")
    return extract_domains(output)


def fetch_ssl(domain):
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                san = cert.get("subjectAltName", [])
                return {d[1] for d in san if d[0] == "DNS"}
    except Exception:
        return set()


def fetch_sitemap(domain):
    urls = set()
    try:
        sitemap_url = f"https://{domain}/sitemap.xml"
        r = requests.get(sitemap_url, timeout=5)
        if r.status_code != 200:
            return urls

        root = ET.fromstring(r.text)
        for loc in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
            urls |= extract_domains(loc.text)
    except Exception:
        pass
    return urls


def main():
    # 每个区域的结果集合
    results = {
        "cn": set(),
        "hk": set(),
        "us": set(),
        "sg": set(),
    }

    for region, roots in ROOT_DOMAINS.items():
        # 先把 ROOT_DOMAINS 本身加入结果（保证至少有这些）
        results[region] |= set(roots)

        for root in roots:
            print(f"[{region}] Fetching: {root}")

            results[region] |= fetch_dns(root)
            results[region] |= fetch_ssl(root)
            results[region] |= fetch_sitemap(root)

    # 直接按区域写回，不再二次分类丢数据
    for region, domains in results.items():
        path = os.path.join(DATA_DIR, f"{region}-source.txt")
        with open(path, "w") as f:
            for d in sorted(domains):
                f.write(d + "\n")

        print(f"[{region}] written {len(domains)} domains to {path}")

    print("Done.")


if __name__ == "__main__":
    main()
