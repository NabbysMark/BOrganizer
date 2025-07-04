import os
import requests
from urllib.parse import urlparse

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