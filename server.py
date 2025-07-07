from flask import Flask, Response, request, abort, send_file
from urllib.parse import unquote
from bs4 import BeautifulSoup
import threading
import requests
import fnmatch
import json
import time
import os

# Server host and port configuration
HOST = '127.0.0.1'
PORT = 7869

app = Flask(__name__)
app.url_map.strict_slashes = False

CONFIG_PATH = 'config.json'
INSTALL_BASE_PATH = 'installBase.ps1'
UNINSTALL_BASE_PATH = 'uninstallBase.ps1'
PREBUILT_DIR = 'prebuiltInstallers'

# Global tag cache: {(owner, repo): [tags]}
TAG_CACHE = {}
TAG_CACHE_LOCK = threading.Lock()

TAG_REFRESH_INTERVAL_MINUTES = 60  # Default: 1 hour

# Create default config.json if it doesn't exist
if not os.path.exists(CONFIG_PATH):
    print("[INFO] config.json not found, creating default config...")
    default_config = {
        "apps": {
            "default": {
                "owner": "your-github-username",
                "repo": "your-repo",
                "binary": "your-app.exe",
                "version": "latest",
                "name": "DefaultApp",
                "folder": "DefaultAppFolder"
            },
            "nitrosensual": {
                "owner": "KRWCLASSIC",
                "repo": "NitroSensual",
                "binary": "nitrosensual.exe",
                "version": "latest",
                "name": "NitroSensual",
                "folder": "NitroSensual"
            },
            "weget": {
                "owner": "KRWCLASSIC",
                "repo": "weget",
                "binary": "weget.exe",
                "version": "latest",
                "name": "Weget",
                "folder": "weget"
            }
        }
    }
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=4)
    print(f"[INFO] Created default {CONFIG_PATH}")

print("[INFO] Loading config.json...")
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = json.load(f)
print("[INFO] Config loaded.")

APPS = config.get('apps', {})

print("[INFO] Reading base install script...")
if not os.path.exists(INSTALL_BASE_PATH):
    raise FileNotFoundError(f"{INSTALL_BASE_PATH} not found. Please provide the base install script.")
with open(INSTALL_BASE_PATH, 'r', encoding='utf-8') as f:
    install_base = f.read()
print("[INFO] Base install script loaded.")

print("[INFO] Reading base uninstall script...")
if not os.path.exists(UNINSTALL_BASE_PATH):
    raise FileNotFoundError(f"{UNINSTALL_BASE_PATH} not found. Please provide the base uninstall script.")
with open(UNINSTALL_BASE_PATH, 'r', encoding='utf-8') as f:
    uninstall_base = f.read()
print("[INFO] Base uninstall script loaded.")

# Ensure prebuilt installers directory exists
os.makedirs(PREBUILT_DIR, exist_ok=True)

# Clean prebuilt installers on boot
for filename in os.listdir(PREBUILT_DIR):
    file_path = os.path.join(PREBUILT_DIR, filename)
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"[INFO] Removed old prebuilt installer: {file_path}")
    except Exception as e:
        print(f"[WARN] Could not remove {file_path}: {e}")

def get_tags(owner, repo):
    key = (owner, repo)
    with TAG_CACHE_LOCK:
        if key in TAG_CACHE:
            return TAG_CACHE[key]
    url = f"https://github.com/{owner}/{repo}/tags"
    headers = {"User-Agent": "Mozilla/5.0"}
    print(f"[INFO] Scraping tags for {owner}/{repo}...")
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"[ERROR] Failed to fetch tags page for {repo}: {resp.status_code}")
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        tag_links = soup.find_all("a", class_="Link--primary Link")
        tags = [tag_link["href"].split("/")[-1] for tag_link in tag_links if tag_link and tag_link["href"]]
        with TAG_CACHE_LOCK:
            TAG_CACHE[key] = tags
        return tags
    except Exception as e:
        print(f"[ERROR] Exception while scraping tags for {repo}: {e}")
        return []

def get_tag_by_version(owner, repo, version_rule):
    tags = get_tags(owner, repo)
    if not tags:
        print(f"[ERROR] No tags found for {repo}")
        return None
    # Wildcard support
    if "*" in version_rule or "?" in version_rule:
        for tag in tags:
            if fnmatch.fnmatch(tag, version_rule):
                print(f"[INFO] Found tag '{tag}' for {repo} using wildcard '{version_rule}'")
                return tag
        print(f"[WARN] No tag matching wildcard '{version_rule}' found for {repo}")
        return None
    if version_rule == "latest":
        print(f"[INFO] Using latest tag '{tags[0]}' for {repo}")
        return tags[0]
    elif version_rule.startswith("latest-"):
        try:
            idx = int(version_rule.split("-")[1])
            if idx < len(tags):
                print(f"[INFO] Using tag '{tags[idx]}' for {repo} (latest-{idx})")
                return tags[idx]
            else:
                print(f"[WARN] Not enough tags for latest-{idx} in {repo}")
                return None
        except Exception:
            print(f"[ERROR] Invalid latest-N format for version_rule '{version_rule}'")
            return None
    elif version_rule == "first":
        print(f"[INFO] Using first tag '{tags[-1]}' for {repo}")
        return tags[-1]
    else:
        # Specific tag
        if version_rule in tags:
            print(f"[INFO] Using specific tag '{version_rule}' for {repo}")
            return version_rule
        else:
            print(f"[WARN] Tag '{version_rule}' not found for {repo}")
            return None

def is_browser_request():
    ua = request.headers.get('User-Agent', '').lower()
    if 'powershell' in ua:
        return False
    return True

def get_html_page():
    with open('IronShell.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/')
def root():
    if is_browser_request():
        return Response(get_html_page(), mimetype='text/html')
    host = request.host_url.rstrip('/')
    ps_script = (
        'Write-Host "IronShell App Installer Server" -ForegroundColor Cyan\n'
        '\n'
        'Write-Host "Quick endpoints:" -ForegroundColor Green\n'
        'Write-Host "  /install/<app>   - Install an app" -ForegroundColor White\n'
        'Write-Host "  /uninstall/<app> - Uninstall an app" -ForegroundColor White\n'
        'Write-Host "  /help            - Full help & usage" -ForegroundColor White\n'
        '\n'
        'Write-Host ""\n'
        'Write-Host "Example usage:" -ForegroundColor Yellow\n'
        f'Write-Host "  iwr {host}/install/app | iex" -ForegroundColor Cyan\n'
        f'Write-Host "  iwr {host}/help | iex" -ForegroundColor Cyan\n'
    )
    return Response(ps_script, mimetype='text/plain')

@app.route('/install/', defaults={'app_name': None})
def install_default(app_name):
    if is_browser_request():
        return Response(get_html_page(), mimetype='text/html')
    default_endpoint = APPS.get('default')
    if not default_endpoint or default_endpoint not in APPS:
        host = request.host_url.rstrip('/')
        ps_script = (
            'Write-Host "Default app is not available on this server." -ForegroundColor Red\n'
            'Write-Host ""\n'
            'Write-Host "Run the following to see available apps:" -ForegroundColor Yellow\n'
            f'Write-Host "iwr {host}/list | iex" -ForegroundColor Cyan\n'
        )
        return Response(ps_script, mimetype='text/plain')
    app_cfg = APPS[default_endpoint]
    owner = app_cfg.get("owner")
    repo = app_cfg.get("repo")
    binary = app_cfg.get("binary")
    display_name = app_cfg.get("name") or repo
    folder_name = app_cfg.get("folder") or repo
    version_rule = app_cfg.get("version", "latest")
    version = get_tag_by_version(owner, repo, version_rule)
    if not version:
        return Response(f'Write-Host "Could not determine version for default app." -ForegroundColor Red', mimetype='text/plain')
    script = install_base
    script = script.replace('$APP_NAME = " "', f'$APP_NAME = "{repo}"')
    script = script.replace('$APP_OWNER = ""', f'$APP_OWNER = "{owner}"')
    script = script.replace('$APP_VERSION = ""', f'$APP_VERSION = "{version}"')
    script = script.replace('$APP_BINARY = ""', f'$APP_BINARY = "{binary}"')
    script = script.replace('$APP_DISPLAYNAME = ""', f'$APP_DISPLAYNAME = "{display_name}"')
    script = script.replace('$APP_FOLDER = ""', f'$APP_FOLDER = "{folder_name}"')
    script = script.replace('/$APP_OWNER/$APP_NAME/releases/download/$APP_VERSION/$APP_NAME.exe',
                            f'/{owner}/{repo}/releases/download/{version}/{binary}')
    return Response(script, mimetype='text/plain')

@app.route('/install/<path:app_name>')
def install(app_name):
    if is_browser_request():
        return Response(get_html_page(), mimetype='text/html')
    # Support /install/app@version syntax
    version_override = None
    unknown_args = []
    if app_name is not None and '@' in app_name:
        app_name, version_override = app_name.split('@', 1)
        app_name = unquote(app_name)
        version_override = unquote(version_override)
    # Accept ?version= and ?v= as version arguments
    q_version = request.args.get('version')
    q_v = request.args.get('v')
    q_vl = request.args.get('vl')
    q_versionlist = request.args.get('versionlist')
    if q_version:
        if version_override and q_version != version_override:
            unknown_args.append('version (conflicts with @version)')
        version_override = q_version
    if q_v:
        if version_override and q_v != version_override:
            unknown_args.append('v (conflicts with @version or ?version)')
        version_override = q_v
    # Detect unknown query args
    for arg in request.args:
        if arg not in ('version', 'v', 'vl', 'versionlist'):
            unknown_args.append(arg)
    if unknown_args:
        host = request.host_url.rstrip('/')
        unknown_args_str = ', '.join(unknown_args)
        ps_script = (
            'Write-Host "Unknown or conflicting arguments provided to /install endpoint:" -ForegroundColor Red\n'
            f'Write-Host "  {unknown_args_str}" -ForegroundColor Yellow\n'
            'Write-Host "\nSupported usage examples:" -ForegroundColor White\n'
            f'Write-Host "  iwr {host}/install/app | iex" -ForegroundColor Cyan\n'
            f'Write-Host "  iwr {host}/install/app?version=1.2.3 | iex" -ForegroundColor Cyan\n'
            f'Write-Host "  iwr {host}/install/app?v=1.2.3 | iex" -ForegroundColor Cyan\n'
            f'Write-Host "  iwr {host}/install/app@1.2.3 | iex" -ForegroundColor Cyan\n'
            f'Write-Host "  iwr {host}/install/app?vl | iex" -ForegroundColor Cyan\n'
            f'Write-Host "  iwr {host}/install/app?versionlist | iex" -ForegroundColor Cyan\n'
        )
        return Response(ps_script, mimetype='text/plain')
    if app_name not in APPS:
        print(f"[WARN] Install requested for unknown app: {app_name}")
        host = request.host_url.rstrip('/')
        ps_script = (
            f'Write-Host "App {app_name} not found on this server." -ForegroundColor Red\n'
            f'Write-Host "Run the following to see available apps:" -ForegroundColor Yellow\n'
            f'Write-Host "iwr {host}/list | iex" -ForegroundColor Cyan\n'
        )
        return Response(ps_script, mimetype='text/plain')
    app_cfg = APPS[app_name]
    owner = app_cfg.get("owner")
    repo = app_cfg.get("repo")
    binary = app_cfg.get("binary")
    display_name = app_cfg.get("name") or repo
    folder_name = app_cfg.get("folder") or repo
    version_rule = version_override if version_override else app_cfg.get("version", "latest")
    # Handle ?vl or ?versionlist
    if q_vl is not None or q_versionlist is not None:
        tags = get_tags(owner, repo)
        if not tags:
            return Response(f'Write-Host "No tags found for {repo}" -ForegroundColor Red', mimetype='text/plain')
        tag_line = ', '.join(tags)
        ps_script = f'Write-Host "Available tags: {tag_line}" -ForegroundColor Yellow'
        return Response(ps_script, mimetype='text/plain')
    # If no version override, use prebuilt installer if available
    if not version_override:
        if app_name in APPS:
            print(f"[INFO] Served prebuilt install script for: {app_name}")
            version = get_tag_by_version(owner, repo, version_rule)
            if version:
                script = install_base
                script = script.replace('$APP_NAME = " "', f'$APP_NAME = "{repo}"')
                script = script.replace('$APP_OWNER = ""', f'$APP_OWNER = "{owner}"')
                script = script.replace('$APP_VERSION = ""', f'$APP_VERSION = "{version}"')
                script = script.replace('$APP_BINARY = ""', f'$APP_BINARY = "{binary}"')
                script = script.replace('$APP_DISPLAYNAME = ""', f'$APP_DISPLAYNAME = "{display_name}"')
                script = script.replace('$APP_FOLDER = ""', f'$APP_FOLDER = "{folder_name}"')
                script = script.replace('/$APP_OWNER/$APP_NAME/releases/download/$APP_VERSION/$APP_NAME.exe',
                                        f'/{owner}/{repo}/releases/download/{version}/{binary}')
                return Response(script, mimetype='text/plain')
    # Otherwise, generate dynamically
    version = get_tag_by_version(owner, repo, version_rule)
    if not version:
        tags = get_tags(owner, repo)
        host = request.host_url.rstrip('/')
        suggestion = ''
        if tags:
            tag_limit = 5
            tag_line = ', '.join(tags[:tag_limit])
            more_count = len(tags) - tag_limit
            if more_count > 0:
                suggestion_lines = [
                    f'Write-Host "Available tags: {tag_line}" -NoNewline -ForegroundColor Yellow; Write-Host " ({more_count} more)" -ForegroundColor DarkGray'
                ]
            else:
                suggestion_lines = [
                    f'Write-Host "Available tags: {tag_line}" -ForegroundColor Yellow'
                ]
            suggestion_lines.append('Write-Host ""')
            suggestion_lines.append(f'Write-Host "Run the following to see all tags:" -ForegroundColor Yellow')
            suggestion_lines.append(f'Write-Host "iwr {host}/install/{app_name}?vl | iex" -ForegroundColor Cyan')
            suggestion_lines.append('Write-Host ""')
            suggestion = '\n'.join(suggestion_lines)
        ps_script = (
            f'Write-Host "Could not find version {version_rule} for {app_name}." -ForegroundColor Red\n'
            'Write-Host ""\n'
            f'{suggestion}\n'
            'Write-Host "Run the following to see available apps:" -ForegroundColor Yellow\n'
            f'Write-Host "iwr {host}/list | iex" -ForegroundColor Cyan\n'
        )
        return Response(ps_script, mimetype='text/plain')
    script = install_base
    script = script.replace('$APP_NAME = " "', f'$APP_NAME = "{repo}"')
    script = script.replace('$APP_OWNER = ""', f'$APP_OWNER = "{owner}"')
    script = script.replace('$APP_VERSION = ""', f'$APP_VERSION = "{version}"')
    script = script.replace('$APP_BINARY = ""', f'$APP_BINARY = "{binary}"')
    script = script.replace('$APP_DISPLAYNAME = ""', f'$APP_DISPLAYNAME = "{display_name}"')
    script = script.replace('$APP_FOLDER = ""', f'$APP_FOLDER = "{folder_name}"')
    script = script.replace('/$APP_OWNER/$APP_NAME/releases/download/$APP_VERSION/$APP_NAME.exe',
                            f'/{owner}/{repo}/releases/download/{version}/{binary}')
    print(f"[INFO] Served install script for: {app_name} (version: {version})")
    return Response(script, mimetype='text/plain')

@app.route('/uninstall/', defaults={'app_name': None})
def uninstall_default(app_name):
    if is_browser_request():
        return Response(get_html_page(), mimetype='text/html')
    default_endpoint = APPS.get('default')
    if not default_endpoint or default_endpoint not in APPS:
        host = request.host_url.rstrip('/')
        ps_script = (
            'Write-Host "Default app is not available for uninstall on this server." -ForegroundColor Red\n'
            'Write-Host ""\n'
            'Write-Host "Run the following to see available apps:" -ForegroundColor Yellow\n'
            f'Write-Host "iwr {host}/list | iex" -ForegroundColor Cyan\n'
        )
        return Response(ps_script, mimetype='text/plain')
    app_cfg = APPS[default_endpoint]
    owner = app_cfg.get("owner")
    repo = app_cfg.get("repo")
    binary = app_cfg.get("binary")
    display_name = app_cfg.get("name") or repo
    folder_name = app_cfg.get("folder") or repo
    script = uninstall_base
    script = script.replace('$APP_NAME = " "', f'$APP_NAME = "{repo}"')
    script = script.replace('$APP_OWNER = ""', f'$APP_OWNER = "{owner}"')
    script = script.replace('$APP_VERSION = ""', f'$APP_VERSION = ""')
    script = script.replace('$APP_BINARY = ""', f'$APP_BINARY = "{binary}"')
    script = script.replace('$APP_DISPLAYNAME = ""', f'$APP_DISPLAYNAME = "{display_name}"')
    script = script.replace('$APP_FOLDER = ""', f'$APP_FOLDER = "{folder_name}"')
    return Response(script, mimetype='text/plain')

@app.route('/uninstall/<app_name>')
def uninstall(app_name):
    if is_browser_request():
        return Response(get_html_page(), mimetype='text/html')
    if app_name not in APPS or app_name == 'default':
        print(f"[WARN] Uninstall requested for unknown app: {app_name}")
        return abort(404, f'App {app_name} not found')
    app_cfg = APPS[app_name]
    owner = app_cfg.get("owner")
    repo = app_cfg.get("repo")
    binary = app_cfg.get("binary")
    display_name = app_cfg.get("name") or repo
    folder_name = app_cfg.get("folder") or repo
    # No version for uninstall
    script = uninstall_base
    script = script.replace('$APP_NAME = " "', f'$APP_NAME = "{repo}"')
    script = script.replace('$APP_OWNER = ""', f'$APP_OWNER = "{owner}"')
    script = script.replace('$APP_VERSION = ""', f'$APP_VERSION = ""')
    script = script.replace('$APP_BINARY = ""', f'$APP_BINARY = "{binary}"')
    script = script.replace('$APP_DISPLAYNAME = ""', f'$APP_DISPLAYNAME = "{display_name}"')
    script = script.replace('$APP_FOLDER = ""', f'$APP_FOLDER = "{folder_name}"')
    print(f"[INFO] Served uninstall script for: {app_name}")
    return Response(script, mimetype='text/plain')

@app.route('/list')
def list_apps():
    if is_browser_request():
        return Response(get_html_page(), mimetype='text/html')
    print("[INFO] Served app list")
    # Exclude 'default' from the list
    ps_script = 'Write-Host "Available apps on this server:" -ForegroundColor Green\n'
    for k in APPS.keys():
        if k != 'default':
            ps_script += f'Write-Host "  {k}" -ForegroundColor Cyan\n'
    return Response(ps_script, mimetype='text/plain')

@app.route('/help')
def help_endpoint():
    if is_browser_request():
        return Response(get_html_page(), mimetype='text/html')
    host = request.host_url.rstrip('/')
    ps_script = (
        'Write-Host "IronShell App Installer Server Help" -ForegroundColor Cyan\n'
        'Write-Host "-------------------------------------" -ForegroundColor DarkGray\n'
        'Write-Host "This server provides PowerShell install scripts for Windows apps." -ForegroundColor Green\n'
        'Write-Host "\nAvailable endpoints:" -ForegroundColor Yellow\n'
        'Write-Host "  /install/<app>   - Get install script for <app>" -ForegroundColor White\n'
        'Write-Host "  /install/        - Get install script for default app" -ForegroundColor White\n'
        'Write-Host "  /uninstall/<app> - Get uninstall script for <app>" -ForegroundColor White\n'
        'Write-Host "  /uninstall/      - Get uninstall script for default app" -ForegroundColor White\n'
        'Write-Host "  /list            - List all available apps" -ForegroundColor White\n'
        'Write-Host "  /help            - Show this help message" -ForegroundColor White\n'
        'Write-Host ""\n'
        'Write-Host "Version selection (any of these work):" -ForegroundColor Yellow\n'
        f'Write-Host "  iwr {host}/install/app?version=1.2.3 | iex" -ForegroundColor Cyan\n'
        f'Write-Host "  iwr {host}/install/app?v=1.2.3 | iex" -ForegroundColor Cyan\n'
        f'Write-Host "  iwr {host}/install/app@1.2.3 | iex" -ForegroundColor Cyan\n'
        'Write-Host ""\n'
        'Write-Host "List available tags for an app:" -ForegroundColor Yellow\n'
        f'Write-Host "  iwr {host}/install/app?vl | iex" -ForegroundColor Cyan\n'
        f'Write-Host "  iwr {host}/install/app?versionlist | iex" -ForegroundColor Cyan\n'
        'Write-Host ""\n'
        'Write-Host "Example usage:" -ForegroundColor Yellow\n'
        f'Write-Host "  iwr {host}/install/app | iex" -ForegroundColor Cyan\n'
        f'Write-Host "  iwr {host}/install/ | iex" -ForegroundColor Cyan\n'
        f'Write-Host "  iwr {host}/uninstall/app | iex" -ForegroundColor Cyan\n'
        f'Write-Host "  iwr {host}/uninstall/ | iex" -ForegroundColor Cyan\n'
        f'Write-Host "  iwr {host}/list | iex" -ForegroundColor Cyan\n'
        'Write-Host ""\n'
        'Write-Host "To see all available apps, run:" -ForegroundColor Yellow\n'
        f'Write-Host "  iwr {host}/list | iex" -ForegroundColor Cyan\n'
    )
    return Response(ps_script, mimetype='text/plain')

@app.errorhandler(404)
def not_found(e):
    if is_browser_request():
        return Response(get_html_page(), mimetype='text/html', status=200)
    host = request.host_url.rstrip('/')
    ps_script = (
        'Write-Host "[ERROR] Endpoint not found!" -ForegroundColor Red\n'
        'Write-Host "You requested a URL that does not exist on this server." -ForegroundColor Yellow\n'
        'Write-Host "\nRun the following to see available endpoints and usage:" -ForegroundColor White\n'
        f'Write-Host "  iwr {host}/help | iex" -ForegroundColor Cyan\n'
        'Write-Host "\nTo list available apps:" -ForegroundColor Yellow\n'
        f'Write-Host "  iwr {host}/list | iex" -ForegroundColor Cyan\n'
    )
    return Response(ps_script, mimetype='text/plain', status=200)

def refresh_tags_and_regen_installers():
    global TAG_CACHE
    while True:
        time.sleep(TAG_REFRESH_INTERVAL_MINUTES * 60)
        print(f"[INFO] Periodic tag refresh started...")
        for endpoint_name, app_cfg in APPS.items():
            owner = app_cfg.get("owner")
            repo = app_cfg.get("repo")
            binary = app_cfg.get("binary")
            version_rule = app_cfg.get("version", "latest")
            display_name = app_cfg.get("name") or repo
            folder_name = app_cfg.get("folder") or repo
            if not all([owner, repo, binary]):
                continue
            old_tags = TAG_CACHE.get((owner, repo), [])
            new_tags = get_tags(owner, repo)
            if not new_tags:
                continue
            if old_tags != new_tags:
                print(f"[INFO] Tags changed for {repo}: {old_tags} -> {new_tags}")
                # Only regenerate if the latest tag changed
                old_latest = old_tags[0] if old_tags else None
                new_latest = new_tags[0]
                if old_latest != new_latest:
                    version = get_tag_by_version(owner, repo, version_rule)
                    if version:
                        script = install_base
                        script = script.replace('$APP_NAME = " "', f'$APP_NAME = "{repo}"')
                        script = script.replace('$APP_OWNER = ""', f'$APP_OWNER = "{owner}"')
                        script = script.replace('$APP_VERSION = ""', f'$APP_VERSION = "{version}"')
                        script = script.replace('$APP_BINARY = ""', f'$APP_BINARY = "{binary}"')
                        script = script.replace('$APP_DISPLAYNAME = ""', f'$APP_DISPLAYNAME = "{display_name}"')
                        script = script.replace('$APP_FOLDER = ""', f'$APP_FOLDER = "{folder_name}"')
                        script = script.replace('/$APP_OWNER/$APP_NAME/releases/download/$APP_VERSION/$APP_NAME.exe',
                                                f'/{owner}/{repo}/releases/download/{version}/{binary}')
                        script_path = os.path.join(PREBUILT_DIR, f'install{endpoint_name}.ps1')
                        with open(script_path, 'w', encoding='utf-8') as f:
                            f.write(script)
                        print(f"[INFO] Refreshed prebuilt installer for {endpoint_name} -> {repo} v{version} at {script_path}")
        print(f"[INFO] Periodic tag refresh complete.")

# Start the background tag refresh thread
threading.Thread(target=refresh_tags_and_regen_installers, daemon=True).start()

if __name__ == '__main__':
    from waitress import serve
    print(f"[INFO] Starting IronShell with Waitress on {HOST}:{PORT}")
    serve(app, host=HOST, port=PORT)