"""Download the two public sources used in this project.

1. collusion.wiki dump (agent edits, May-July 2026, PII redacted).
2. ProWiki RecentChanges pages for DSE wiki and three sibling wikis,
   10,000 days back, one line per edit (all=1). This is the human baseline.

Run: python src/fetch_data.py
Note: wikiservice.at logs visitor IP addresses (stated on collusion.wiki).
"""
import pathlib
import subprocess
import zipfile

RAW = pathlib.Path(__file__).resolve().parents[1] / "data" / "raw"
CW = RAW / "collusion_wiki"
RC = RAW / "prowiki_rc"
UA = "Mozilla/5.0 (research; Apart AI incident response sprint 2026)"

CW_FILES = ["full-wiki-logs.zip", "site-coverage.csv", "coverage-gaps.csv",
            "other-wikis.json.gz", "shortener-logs.json.gz"]
WIKIS = ["dse", "probier", "fractal", "wiki4d"]


def curl(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print("kept   ", dest.name)
        return
    subprocess.run(["curl", "-sL", "--max-time", "120", "-A", UA, "-o", str(dest), url], check=True)
    print("fetched", dest.name, dest.stat().st_size, "bytes")


def main():
    for f in CW_FILES:
        curl(f"https://collusion.wiki/explorer/download/{f}", CW / f)
    with zipfile.ZipFile(CW / "full-wiki-logs.zip") as z:
        z.extractall(CW)
    for w in WIKIS:
        curl(f"https://www.wikiservice.at/{w}/wiki.cgi?action=rc&days=10000&all=1",
             RC / f"rc_{w}_10000.html")


if __name__ == "__main__":
    main()
