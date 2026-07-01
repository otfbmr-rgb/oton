import json
import os
import sys
import urllib.request

REPO = os.getenv("GITHUB_REPOSITORY", "otfbmr-rgb/oton")
TAG = os.getenv("GITHUB_RELEASE_TAG", "v0.1.1")
TOKEN = os.getenv("GITHUB_TOKEN")

if not TOKEN:
    sys.exit("Missing GITHUB_TOKEN environment variable.")

with open("RELEASE_BODY.md", "r", encoding="utf-8") as handle:
    body = handle.read()

payload = {
    "tag_name": TAG,
    "name": TAG,
    "body": body,
    "draft": False,
    "prerelease": False,
}

url = f"https://api.github.com/repos/{REPO}/releases"
req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"token {TOKEN}",
        "User-Agent": "garami-release-script",
    },
)

try:
    with urllib.request.urlopen(req) as response:
        result = json.load(response)
        print("Release created:", result.get("html_url"))
except urllib.error.HTTPError as exc:
    print("Failed to create release:", exc.code, exc.reason)
    print(exc.read().decode("utf-8"))
    sys.exit(1)
