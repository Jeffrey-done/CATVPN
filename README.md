# CATVPN subscription aggregator

This repository collects public Clash/Mihomo subscription sources, normalizes and deduplicates their proxy definitions, measures TCP connection latency, and publishes a client-ready subscription file.

The updater runs once per day via `scripts/discover_github.py`. It searches public GitHub repositories for subscription-like files, fetches only candidates whose paths look relevant, accepts a file only when it parses into Clash proxy entries, and then sends accepted sources through the same deduplication and reachability checks. The discovery result is stored in `discovered_sources.yaml` for review and reproducibility.

## Generated endpoints

After GitHub Actions runs, the client can use:

```text
https://raw.githubusercontent.com/<owner>/<repo>/main/public/clash.yaml
```

`public/status.json` contains source counts and the latest update result.

## Local run

```powershell
pip install -r requirements.txt
python scripts/aggregate.py --no-check
python -m pytest
```

To run discovery locally, set a GitHub token for a higher API limit and run `python scripts/discover_github.py`. GitHub Actions supplies `GITHUB_TOKEN` automatically.

The first client should use Mihomo/Clash Meta as its network core and consume `public/clash.yaml`. The user interface can then show the generated proxy list and let the core perform live URL testing and switching.

## Client direction

The planned client is a Clash Verge-style extensible desktop application:

- **Core:** bundled Mihomo process, controlled through its local REST API
- **Built-in Provider:** this repository's generated `public/clash.yaml` URL
- **Extensions:** provider adapters, profile import/export, routing rule packs, themes, and updater modules
- **UI:** profile list, node list, latency/status, system proxy toggle, and tray controls

The aggregator remains independent from the client, so the same generated URL can be consumed by the desktop app and existing Clash-compatible clients.

## Run the desktop shell

For local development, the desktop shell reads `../public/clash.yaml`. To use your GitHub repository, change the Provider in `client/settings.json` to:

```json
{
  "subscription": {
    "provider": "github-raw",
    "url": "https://raw.githubusercontent.com/<user>/<repo>/main/public/clash.yaml"
  }
}
```

Then run:

```powershell
cd client
npm install
npm start
```

The shell includes Mihomo Meta `v1.19.28` for Windows amd64, starts it from `client/resources/mihomo/mihomo.exe`, connects to its API at `127.0.0.1:9090`, and provides a tray menu with a system-proxy toggle.

The Mihomo core is bundled directly in the client. Build the Windows NSIS installer locally with `cd client; pnpm install; pnpm build:win`; GitHub Actions is intentionally limited to daily subscription discovery and refresh.
