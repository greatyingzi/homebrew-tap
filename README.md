# Homebrew tap

Casks for my own macOS apps. One tap for all of them — `Casks/` holds one file per
application, so nothing here needs a repository (or a workflow) per app.

```bash
brew tap greatyingzi/tap
brew install --cask sparkwatch      # menu bar monitor for a DGX Spark fleet
brew install --cask macfan          # menu bar fan control / AppleSMC utility
```

Upgrade with `brew upgrade --cask <name>`; `brew uninstall --cask <name>` removes
the app, and `--zap` also removes its settings.

## First launch

These apps are signed ad-hoc rather than notarised — notarisation needs a paid
Apple Developer account — so macOS quarantines what Homebrew downloads and the
first launch needs one approval. Homebrew 7 removed its `--no-quarantine` flag, so
that step cannot be skipped from here:

```bash
xattr -dr com.apple.quarantine /Applications/<App>.app
```

The recursive `-r` matters (the attribute is on the inner executable too). Or
right-click the app → Open → Open again; if macOS only offers "Done", use
System Settings → Privacy & Security → Open Anyway.

## How a cask is kept current

`Casks/*.rb` is generated, not hand-written. Each app is one stanza in
`.github/casks.json`; `.github/sync_casks.py` renders the cask from that project's
cask template — read from the **released tag**, so this repository cannot drift
from the file the project's own release tooling renders — and hashes the
**published** release asset, because a locally built DMG is not byte-identical to
the one CI built.

`.github/workflows/sync-cask.yml` runs it daily (and on manual dispatch), inside
this repository, with this repository's own token: no secrets, no personal token.

Adding an app is one stanza in `casks.json`. Check locally before pushing:

```bash
python3 .github/sync_casks.py --dry-run          # render, change nothing
python3 .github/sync_casks.py sparkwatch         # one app; commits and pushes
```

The daily job exists because a stale cask fails silently: every user's
`brew upgrade` reports "already up to date" while newer releases exist. This tap
was once four versions behind without a single signal.
