# IronShell

**IronShell** is a self-hosted flask-waitress server for distributing Windows applications via PowerShell one-liners. It dynamically generates PowerShell installer scripts for your apps, supporting version selection, custom install folders, and user-friendly display names.

> On boot, the server generates install scripts for all apps in `config.json` and saves them to `prebuiltInstallers/`, if you only want generated scripts, you can just take them from there. I plan to add a way to make server work only in script generation mode or easy CLI creator via arguments, might even create new app for it.

## krwutils CLI app

Still in development, but it simplifies install proccess of my apps.

## Future

- Autoupdate server scripts on boot. (pufferpannel only? preboot script)
- Linux Support/Port with .sh scripts or krwutils only port.

## Features

- Serve PowerShell install scripts for any app hosted on GitHub
- Supports custom binary names, install folders, and display names
- Flexible version selection (latest, specific, wildcards, etc.)
- Easy to extend: just edit `config.json`
- `/list` endpoint for discoverability
- User-friendly error messages and logs

## Requirements

- Python 3.7+     // Tho i recommend 3.11
- flask           // For Server framework
- waitress        // For WSGI part of the server
- requests        // For Retriving GitHub page to scrape
- beautifulsoup4  // For scraping version tags

## Quick Start

1. Clone this repo and `cd` into it.
2. Edit `config.json` to add your apps.
3. Run the server:

   ```sh
   python server.py
   ```

4. From a Windows machine, install an app with:

   ```powershell
   iwr http://yourserver/install/weget | iex
   ```

   Or list available apps:

   ```powershell
   iwr http://yourserver/list | iex
   ```

> **Want to use a custom domain instead of an IP address? Or just general help with setting this project up?**  
> See the [generalSetup.md](generalSetup.md) guide for setup instructions.

## Example Usage

- To install the latest version of `SASM` from Nuitka builds:

  ```powershell
  iwr https://utils.krwclassic.com/install/sasm-nuitka | iex
  ```

- To see all available apps:

  ```powershell
  iwr https://utils.krwclassic.com/list | iex
  ```

## Configuration

The server uses a `config.json` file to define which apps are available for installation and how their installers are generated.

### Structure

```json
{
    "apps": {
        "endpoint-name": {
            "owner": "GitHubOwner",         // (required) GitHub username or organization
            "repo": "RepositoryName",       // (required) GitHub repository name
            "binary": "binary.exe",         // (required) Name of the binary to download from the release/tag
            "version": "latest",            // (optional) Version/tag selection rule (see below)
            "name": "Display Name",         // (optional) User-friendly name for display in the installer (defaults to repo)
            "folder": "installfolder"       // (optional) Folder name for installation (defaults to repo)
        }
        // ... more apps ...
    }
}
```

### Field Descriptions

- **endpoint-name**: The name used in the URL, e.g. `/install/weget`.
- **owner**: The GitHub username or organization that owns the repository.
- **repo**: The repository name on GitHub.
- **binary**: The name of the binary file to download from the release/tag assets.
- **version**: (Optional) Controls which tag to use for the download. Supports:
  - `"latest"` — The newest tag (default)
  - `"latest-N"` — The Nth latest tag (e.g., `latest-1` is the previous tag)
  - `"first"` — The oldest tag
  - `"<tag>"` — A specific tag name
  - Wildcards: `"*-Nuitka"`, `"?.?.?-Nuitka"` — Uses the first tag matching the pattern (shell-style wildcards)
- **name**: (Optional) User-friendly display name for the app, shown in the PowerShell output. Defaults to the repo name if not set.
- **folder**: (Optional) The folder name under `%APPDATA%\<owner>\<folder>` where the app will be installed. Defaults to the repo name if not set.

### Example

```json
{
    "apps": {
        "sasm-nuitka": {
            "owner": "KRWCLASSIC",
            "repo": "Steam-Account-Switcher-Manager",
            "binary": "sasm.exe",
            "version": "*-Nuitka",
            "name": "SASM",
            "folder": "steamaccountswitchermanager"
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
```

### Notes

- All fields except `name` and `folder` are required for each app.
- The `version` field supports wildcards (`*`, `?`) for flexible tag selection.
- The `name` field is used for all user-facing output in the PowerShell installer.
- The `folder` field controls the install directory name; use it to match the folder your app creates or expects.
- The endpoint name (e.g., `weget`) is what users will use in the install URL: `iwr http://yourserver/install/weget | iex`
