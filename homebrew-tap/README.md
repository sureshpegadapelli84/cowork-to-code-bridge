# homebrew-tap

Homebrew tap for [cowork-to-code-bridge](https://github.com/abhinaykrupa/cowork-to-code-bridge).

## Usage

```bash
brew tap abhinaykrupa/tap
brew install cowork-to-code-bridge
brew services start cowork-to-code-bridge
```

Then run the one-time setup:

```bash
cowork-to-code-bridge-selfcheck
```

## What's in this tap

| Formula | Description |
|---|---|
| `cowork-to-code-bridge` | Bridge daemon + CLI tools (`selfcheck`, `uninstall`) |

## How to deploy this tap

1. Create a **public** repo named `homebrew-tap` at `github.com/abhinaykrupa/homebrew-tap`
2. Copy `Formula/cowork-to-code-bridge.rb` into it
3. Fill in the correct `sha256` after the first PyPI publish:
   ```bash
   curl -sL https://pypi.org/pypi/cowork-to-code-bridge/json | python3 -c \
     "import json,sys; r=json.load(sys.stdin); \
      [print(f['digests']['sha256']) for f in r['urls'] if f['packagetype']=='sdist']"
   ```
4. Push — the tap is live immediately

The `bump-formula.yml` workflow in the main repo updates the sha256 automatically on each release tag.
