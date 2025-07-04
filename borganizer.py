import requests
import os
import sys
from urllib.parse import urlparse

VERSION = "1.0.0"

def parse_packagesettings_from_text(text):
    settings = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or " BOOM " not in line:
            continue

        key, value = line.split(" BOOM ", 1)
        key = key.strip()
        value = value.strip()

        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.lower() == "true":
            value = True
        elif value.lower() == "false":
            value = False
        else:
            try:
                if "." in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass

        settings[key] = value

    return settings

def print_settings(settings):
    if not settings:
        print("No packagesettings.nls found or file is empty.")
    else:
        print("Library Information from packagesettings.nls:")
        for k, v in settings.items():
            print(f"  {k}: {v}")

def check_packagesettings_exists(user, repo):
    url = f"https://api.github.com/repos/{user}/{repo}/contents/packagesettings.nls"
    r = requests.get(url)
    if r.status_code == 200:
        return True
    elif r.status_code == 404:
        return False
    else:
        r.raise_for_status()

def get_packagesettings_content(user, repo):
    url = f"https://api.github.com/repos/{user}/{repo}/contents/packagesettings.nls"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    import base64
    content_encoded = data.get("content", "")
    content_bytes = base64.b64decode(content_encoded)
    return content_bytes.decode("utf-8")

def downloadpackage(repo_url, output_dir=None):
    parsed = urlparse(repo_url)
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 2:
        raise ValueError("Invalid GitHub repository URL")

    user, repo = parts[0], parts[1].replace(".git", "")

    if os.name == "nt":
        localappdata = os.environ.get("LOCALAPPDATA")
        if localappdata is None:
            print("Warning: LOCALAPPDATA not found, using current directory instead.")
            base_dir = os.getcwd()
        else:
            base_dir = os.path.join(localappdata, "nscript_libs")
    else:
        base_dir = os.path.expanduser("~/.nscript_libs")

    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
        print(f"Created directory: {base_dir}")

    if output_dir is None:
        output_dir = os.path.join(base_dir, repo)
    else:
        output_dir = os.path.join(base_dir, output_dir)

    if not check_packagesettings_exists(user, repo):
        print(f"Error: 'packagesettings.nls' not found in repository '{user}/{repo}'. Download aborted.")
        return

    api_url = f"https://api.github.com/repos/{user}/{repo}/contents"

    def download_contents(url, local_path):
        response = requests.get(url)
        response.raise_for_status()
        items = response.json()

        if not os.path.exists(local_path):
            os.makedirs(local_path)

        for item in items:
            item_path = os.path.join(local_path, item["name"])
            if item["type"] == "file":
                file_data = requests.get(item["download_url"])
                with open(item_path, "wb") as f:
                    f.write(file_data.content)
                print(f"Downloaded file: {item_path}")
            elif item["type"] == "dir":
                download_contents(item["url"], item_path)

    download_contents(api_url, output_dir)
    print(f"\nDownload complete. Repository saved in folder: {output_dir}")

    settings_path = os.path.join(output_dir, "packagesettings.nls")
    if os.path.isfile(settings_path):
        with open(settings_path, "r") as f:
            content = f.read()
        settings = parse_packagesettings_from_text(content)
        print_settings(settings)
    else:
        print("Warning: packagesettings.nls not found after download (unexpected).")

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