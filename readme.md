# IronShell

**IronShell** is a self-hosted flask-waitress server for distributing Windows applications via PowerShell one-liners. It dynamically generates PowerShell installer scripts for your apps, supporting version selection, custom install folders, and user-friendly display names.

## krwutils CLI app

Still in development, but it simplifies install proccess of my apps.

> yeah thats a lie, i didnt even start it.

## TODO

- Force remove installation folder on uninstall or config value to configure what should be deleted aswell (with * meaninng force entire folder removal)
- Create shortcuts on install
- Non-binary apps support (.py script with wrappers etc., additional subscripts for checking machine env. like installed python etc.) | 25% done (via autorun prefix, left to do: env checking, dependencies, run helpers, winget integration? etc.)
- Clean up base scripts and fix ordering of variables (huge mess)

## Future

- Autoupdate server (install/uninstall scripts) on boot. (pufferpannel only? preboot script)
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
            "autorun": false,               // (optional) Autorun app after install (default: false)
            "autorunPrefix": "",            // (optional) Prefix for autorun command (e.g. "cmd /k", "python -m")
            "autorunArguments": ""          // (optional) Arguments for autorun command
        },
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
- **autorun**: (Optional, default: false) If true, the app will be run automatically after installation completes.
- **autorunPrefix**: (Optional) If set, this prefix will be prepended to the autorun command (e.g. `python -m`, `cmd /k`). If set, the autorun command will be launched in a new PowerShell window.
- **autorunArguments**: (Optional) Arguments to pass to the autorun command (e.g. `--help`).

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
            "folder": "steamaccountswitchermanager",
            "autorun": false,
            "autorunPrefix": "",
            "autorunArguments": ""
        },
        "my-python-app": {
            "owner": "me",
            "repo": "my-python-repo",
            "binary": "myscript.py",
            "version": "latest",
            "name": "MyPythonApp",
            "folder": "mypythonapp",
            "autorun": true,
            "autorunPrefix": "python -m",
            "autorunArguments": "--help"
        }
    }
}
```

### Autorun Behavior

If `autorun` is set to true, the installer will automatically run the app after installation:

- If `autorunPrefix` is set (e.g. `python`, `cmd /k`), the command will be launched in a **new PowerShell window** so apps dont collide with execution of the installer.
- If `autorunPrefix` is not set, the binary will be run directly in the current session.
- `autorunArguments` are appended to the command.

**Examples:**

- Run a CLI app and keep the window open:

  ```json
  "autorun": true,
  "autorunPrefix": "cmd /k",
  "autorunArguments": ""
  ```

- Run a Python script:

  ```json
  "autorun": true,
  "autorunPrefix": "python -m",
  "autorunArguments": "--help"
  ```

### Notes

- All fields except `name` and `folder` are required for each app.
- The `version` field supports wildcards (`*`, `?`) for flexible tag selection.
- The `name` field is used for all user-facing output in the PowerShell installer.
- The `folder` field controls the install directory name; use it to match the folder your app creates or expects.
- The endpoint name (e.g., `weget`) is what users will use in the install URL: `iwr http://yourserver/install/weget | iex`
