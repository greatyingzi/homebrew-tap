#!/usr/bin/env python3
"""Render every cask in this tap from its project's latest release.

    python3 .github/sync_casks.py            # all casks
    python3 .github/sync_casks.py sparkwatch # just one

The list of applications lives in casks.json: adding an app is one stanza there,
not another workflow. Each entry names the project repository, the release asset
to hash, and the cask template inside that repository — the template is read from
the released tag (falling back to the default branch), so the file rendered here
is the same file the project's own release tooling would render, and the two
cannot drift.

The digest always comes from the *published* release asset, downloaded here and
hashed locally: a locally built DMG is not byte-identical to the one CI built, so
hashing anything else would produce a cask whose checksum fails for every user.

Everything is committed per cask so the history says which app moved when. Nothing
is pushed by hand: this runs either on the tap's daily schedule or from a manual
dispatch, both inside the tap repository, whose own token can write to it.
"""

import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = ROOT / ".github" / "casks.json"
SCRATCH = pathlib.Path("/tmp/sparkwatch-cask-sync")


def gh(*args: str) -> str:
    result = subprocess.run(
        ("gh", *args), capture_output=True, text=True
    )
    if result.returncode != 0:
        raise SystemExit(f"gh {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def git(*args: str) -> None:
    subprocess.run(("git", "-C", str(ROOT), *args), check=True)


def template_for(repo: str, path: str, tag: str) -> str:
    """The cask template, preferring the released tag for reproducibility."""
    for ref in (tag, None):
        spec = f"repos/{repo}/contents/{path}" + (f"?ref={ref}" if ref else "")
        try:
            content = gh("api", spec, "--jq", ".content")
        except SystemExit:
            continue
        if content.strip():
            print(f"    template from {ref or 'the default branch'}")
            import base64

            return base64.b64decode(content).decode()
    raise SystemExit(f"could not read {path} in {repo} at {tag} or the default branch")


def digest_of(repo: str, tag: str, asset: str) -> str:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    gh("release", "download", tag, "-R", repo, "--pattern", asset,
       "--dir", str(SCRATCH), "--clobber")
    path = SCRATCH / asset
    if not path.exists():
        raise SystemExit(f"{asset} was not attached to {tag}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    only = args[0].strip() if args else ""
    entries = json.loads(CONFIG.read_text())
    changed = []

    for entry in entries:
        cask, repo = entry["cask"], entry["repo"]
        if only and only != cask:
            continue

        print(f"=== {cask} ({repo})")
        tag = gh("api", f"repos/{repo}/releases/latest", "--jq", ".tag_name").strip()
        if not tag or tag == "null":
            raise SystemExit(f"{repo} has no release to sync from")
        version = tag[1:] if tag.startswith("v") else tag
        print(f"    latest release: {tag}")

        template = template_for(repo, entry["template"], tag)
        digest = digest_of(repo, tag, entry["asset"].replace("{v}", version))
        print(f"    digest of the published asset: {digest}")

        rendered = template.replace("{{VERSION}}", version).replace("{{SHA256}}", digest)
        if "{{" in rendered or "}}" in rendered:
            raise SystemExit(f"{cask}: an unsubstituted placeholder survived")
        if "replace with" in rendered.lower():
            raise SystemExit(f"{cask}: the template still holds a placeholder")

        target = ROOT / "Casks" / f"{cask}.rb"
        unchanged = target.exists() and target.read_text() == rendered
        if dry:
            if unchanged:
                print(f"    Casks/{cask}.rb already matches {tag}")
            else:
                print(f"    Casks/{cask}.rb would be {'updated' if target.exists() else 'created'}:")
                print("\n".join("      " + line for line in rendered.splitlines()))
            continue
        if unchanged:
            print(f"    already matches {tag}, nothing to do")
            continue

        target.write_text(rendered)
        git("add", f"Casks/{cask}.rb")
        git("-c", f"user.name={cask} cask sync",
            "-c", "user.email=greatyingzi@users.noreply.github.com",
            "commit", "-q", "-m", f"{cask} {version} (scheduled sync)")
        changed.append(f"{cask} {version}")
        print(f"    committed Casks/{cask}.rb at {version}")

    if not changed:
        print("no cask needed updating")
        return 0

    git("push")
    print("pushed: " + ", ".join(changed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
