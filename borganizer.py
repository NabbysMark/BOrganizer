import requests
import os
import sys
from urllib.parse import urlparse
from utils import parse_packagesettings_from_text
from utils import check_packagesettings_exists
from utils import downloadpackage
from utils import print_settings

VERSION = "1.0.0"

def get_packagesettings_content(user, repo):
    url = f"https://api.github.com/repos/{user}/{repo}/contents/packagesettings.nls"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    import base64
    content_encoded = data.get("content", "")
    content_bytes = base64.b64decode(content_encoded)
    return content_bytes.decode("utf-8")

def info(repo_url):
    parsed = urlparse(repo_url)
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 2:
        print("Invalid GitHub repository URL")
        return

    user, repo = parts[0], parts[1].replace(".git", "")

    try:
        if not check_packagesettings_exists(user, repo):
            print(f"No packagesettings.nls found in repository '{user}/{repo}'.")
            return
        content = get_packagesettings_content(user, repo)
        settings = parse_packagesettings_from_text(content)
        print_settings(settings)
    except Exception as e:
        print(f"Error retrieving packagesettings.nls: {e}")

def main():
    if len(sys.argv) == 2 and sys.argv[1] in ("-v", "--version"):
        print(VERSION)
    elif len(sys.argv) == 3 and sys.argv[1] == "install":
        repo_url = sys.argv[2]
        try:
            downloadpackage(repo_url)
        except Exception as e:
            print(f"Error: {e}")
    elif len(sys.argv) == 3 and sys.argv[1] == "info":
        repo_url = sys.argv[2]
        info(repo_url)
    elif len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        print("Usage:")
        print("  python main.py -v                       Show version")
        print("  python main.py install <repo_url>      Download GitHub repository (requires packagesettings.nls)")
        print("  python main.py info <repo_url>         Show info from packagesettings.nls")
    else:
        print("Invalid usage. Use -h for help.")

if __name__ == "__main__":
    main()