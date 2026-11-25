#!/usr/bin/env python3
"""Bootstrap the StudentLedger TeamCity project through the REST API.

Creates the project, a Git VCS root, a build configuration that builds the
Docker image on every branch and pushes it to Docker Hub for dev and prod.

The script uses a TeamCity access token (Profile -> Access Tokens) sent as a
Bearer token; JSON requests with Bearer authentication bypass the CSRF check.

Usage:
  TEAMCITY_URL=http://192.168.56.11:8111 \
  TEAMCITY_TOKEN=<access token> \
  DOCKERHUB_USER=ahdyshba DOCKERHUB_TOKEN=<docker hub token> \
  python3 ci/teamcity/bootstrap.py
"""
import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("TEAMCITY_URL", "http://192.168.56.11:8111").rstrip("/")
TOKEN = os.environ["TEAMCITY_TOKEN"]
DOCKERHUB_USER = os.environ.get("DOCKERHUB_USER", "ahdyshba")
DOCKERHUB_TOKEN = os.environ["DOCKERHUB_TOKEN"]

PROJECT_ID = "StudentLedger"
VCS_ID = "SLCA_GitHub"
BUILD_ID = "StudentLedger_Build"
REPO = "https://github.com/PervuhinRoman/SLCA.git"

BUILD_SCRIPT = """set -e
IMAGE="%DOCKERHUB_USER%/studentledger"
BRANCH="%teamcity.build.branch%"
SAFE_BRANCH=$(echo "$BRANCH" | tr '/' '-')
docker build --pull -t "$IMAGE:%build.number%" .
docker tag "$IMAGE:%build.number%" "$IMAGE:$SAFE_BRANCH"
docker image ls "$IMAGE"
"""

PUSH_SCRIPT = """set -e
BRANCH="%teamcity.build.branch%"
if [ "$BRANCH" != "dev" ] && [ "$BRANCH" != "prod" ]; then
  echo "Ветка $BRANCH: публикация в Docker Hub не требуется."
  exit 0
fi
echo "%DOCKERHUB_TOKEN%" | docker login -u "%DOCKERHUB_USER%" --password-stdin
docker push "%DOCKERHUB_USER%/studentledger:%build.number%"
docker push "%DOCKERHUB_USER%/studentledger:$BRANCH"
docker logout
"""


def request(method, path, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Authorization", "Bearer " + TOKEN)
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8", "replace")


def create(path, payload, label):
    status, text = request("POST", path, payload)
    if status in (200, 201):
        print(f"[ok] {label}")
        return True
    if status == 400 and ("already exists" in text.lower() or "duplicate" in text.lower()):
        print(f"[skip] {label}: уже существует")
        return True
    print(f"[fail] {label}: HTTP {status}\n{text[:800]}", file=sys.stderr)
    return False


def main() -> int:
    ok = True
    ok &= create("/app/rest/projects", {
        "name": "StudentLedger",
        "id": PROJECT_ID,
        "description": "Учебная ИС учёта успеваемости",
        "parentProject": {"id": "_Root"},
    }, "project")

    ok &= create("/app/rest/vcs-roots", {
        "name": "SLCA GitHub",
        "id": VCS_ID,
        "vcsName": "jetbrains.git",
        "project": {"id": PROJECT_ID},
        "properties": {"property": [
            {"name": "url", "value": REPO},
            {"name": "branch", "value": "refs/heads/dev"},
            {"name": "teamcity:branchSpec", "value": "+:refs/heads/*"},
            {"name": "authMethod", "value": "ANONYMOUS"},
            {"name": "agent.gitPath", "value": "git"},
        ]},
    }, "vcs root")

    ok &= create("/app/rest/buildTypes", {
        "name": "Build and push image",
        "id": BUILD_ID,
        "project": {"id": PROJECT_ID},
        "vcs-root-entries": {"vcs-root-entry": [
            {"vcs-root": {"id": VCS_ID}, "checkout-rules": ""},
        ]},
    }, "build type")

    parameters = [
        {"name": "DOCKERHUB_USER", "value": DOCKERHUB_USER},
        {"name": "DOCKERHUB_TOKEN", "value": DOCKERHUB_TOKEN,
         "type": {"rawValue": "password"}},
        {"name": "env.DOCKER_BUILDKIT", "value": "1"},
    ]
    for parameter in parameters:
        ok &= create(f"/app/rest/buildTypes/id:{BUILD_ID}/parameters",
                     parameter, f"parameter {parameter['name']}")

    for name, script in (("Build image", BUILD_SCRIPT), ("Push image", PUSH_SCRIPT)):
        ok &= create(f"/app/rest/buildTypes/id:{BUILD_ID}/steps", {
            "name": name,
            "type": "simpleRunner",
            "properties": {"property": [
                {"name": "use.custom.script", "value": "true"},
                {"name": "script.content", "value": script},
                {"name": "teamcity.step.mode", "value": "default"},
            ]},
        }, f"step {name}")

    ok &= create(f"/app/rest/buildTypes/id:{BUILD_ID}/triggers", {
        "type": "vcsTrigger",
        "properties": {"property": [
            {"name": "branchFilter", "value": "+:refs/heads/*"},
        ]},
    }, "VCS trigger")

    print(f"TeamCity project: {BASE}/project/{PROJECT_ID}")
    print(f"Build configuration: {BASE}/buildConfiguration/{BUILD_ID}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
