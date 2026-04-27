import yaml
import os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "..", "data")
ROOT_DIR = os.path.join(BASE, "..", "..")

REGIONS = ["hk", "us", "sg"]

def load_domains(path):
    domains = []
    with open(path) as f:
        for line in f:
            d = line.strip()
            if d:
                domains.append(d)
    return domains

def write_list(region, domains):
    with open(f"{ROOT_DIR}/huatai_{region}.list", "w") as f:
        for d in domains:
            if d.startswith("KEYWORD:"):
                f.write(f"DOMAIN-KEYWORD,{d[8:]},DIRECT\n")
            else:
                f.write(f"DOMAIN-SUFFIX,{d},DIRECT\n")

def write_yaml(region, domains):
    payload = []
    for d in domains:
        if d.startswith("KEYWORD:"):
            payload.append(f"DOMAIN-KEYWORD,{d[8:]}")
        else:
            payload.append(f"DOMAIN-SUFFIX,{d}")

    with open(f"{ROOT_DIR}/huatai_{region}.yaml", "w") as f:
        yaml.dump({"payload": payload}, f, allow_unicode=True)

def write_srs(region, domains):
    with open(f"{ROOT_DIR}/huatai_{region}.srs", "w") as f:
        for d in domains:
            if d.startswith("KEYWORD:"):
                f.write(f"DOMAIN-KEYWORD,{d[8:]}\n")
            else:
                f.write(f"DOMAIN-SUFFIX,{d}\n")

def main():
    for region in REGIONS:
        path = os.path.join(DATA_DIR, f"{region}.txt")
        domains = load_domains(path)

        write_list(region, domains)
        write_yaml(region, domains)
        write_srs(region, domains)

if __name__ == "__main__":
    main()

