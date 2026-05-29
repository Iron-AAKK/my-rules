import os

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
    DATA_DIR = os.path.join(BASE_DIR, "..", "data")
    
    domains = set()
    for f_name in ["us_stock_backbone_base.txt", "us_stock_backbone_discovered.txt"]:
        path = os.path.join(DATA_DIR, f_name)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    d = line.strip().replace("DOMAIN-SUFFIX,", "").replace("+.", "").replace("DOMAIN,", "")
                    if d: domains.add(d)

    sorted_domains = sorted(list(domains))
    
    # 格式 1: yaml ( payload: \n - +.domain )
    with open(os.path.join(ROOT_DIR, "us_stock_backbone.yaml"), "w", encoding="utf-8") as f:
        f.write("payload:\n")
        for d in sorted_domains: f.write(f"  - +.{d}\n")
    
    # 格式 2: list ( +.domain )
    with open(os.path.join(ROOT_DIR, "us_stock_backbone.list"), "w", encoding="utf-8") as f:
        for d in sorted_domains: f.write(f"+.{d}\n")
        
    # 格式 3: srs ( DOMAIN-SUFFIX,domain )
    with open(os.path.join(ROOT_DIR, "us_stock_backbone.srs"), "w", encoding="utf-8") as f:
        for d in sorted_domains: f.write(f"DOMAIN-SUFFIX,{d}\n")

if __name__ == "__main__":
    main()
