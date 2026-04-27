import subprocess
import ssl
import socket
import re
import requests
from urllib.parse import urljoin
import xml.etree.ElementTree as ET
import os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "..", "data")

ROOT_DOMAINS = {
    "hk": ["htsc.com.hk", "htsc.hk", "htisec.com", "htisec.hk"],
    "us": ["htsc-us.com", "htsc-usa.com", "htamusa.com", "htscusa.com"],
    "sg": ["htsc.com.sg", "htsc.sg", "htisg.com", "htisec.com.sg"],
}

def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True)
    except:
        return ""

def extract_domains(text):
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
    except:
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
    except:
        pass
    return urls

def classify(domain):
    if ".hk" in domain:
        return "hk"
    if ".sg" in domain:
        return "sg"
    if "usa" in domain or "-us" in domain:
        return "us"
    return None

def main():
    results = {"hk": set(), "us": set(), "sg": set()}

    for region, roots in ROOT_DOMAINS.items():
        for root in roots:
            print(f"Fetching: {root}")

            results[region] |= fetch_dns(root)
            results[region] |= fetch_ssl(root)
            results[region] |= fetch_sitemap(root)

    final = {"hk": set(), "us": set(), "sg": set()}
    for region in results:
        for d in results[region]:
            c = classify(d)
            if c:
                final[c].add(d)

    for region in final:
        path = os.path.join(DATA_DIR, f"{region}-source.txt")
        with open(path, "w") as f:
            for d in sorted(final[region]):
                f.write(d + "\n")

    print("Done.")

if __name__ == "__main__":
    main()
