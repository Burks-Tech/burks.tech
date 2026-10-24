#!/usr/bin/env bash
# Build the site into ./public. Cloudflare Workers Builds runs this on every push;
# run it locally the same way. Branches other than main also build drafts.
set -euo pipefail

want="${HUGO_VERSION:-0.168.0}"
have="$(hugo version)"
case "$have" in
  *"v${want}"*) ;;
  *) echo "build.sh: need Hugo v${want}, found: ${have}" >&2; exit 1 ;;
esac

args=(--gc --minify --cleanDestinationDir)
branch="${WORKERS_CI_BRANCH:-}"
if [ -n "$branch" ] && [ "$branch" != "main" ]; then
  args+=(--buildDrafts --buildFuture)
fi
hugo "${args[@]}"

# The CSP in _headers allows the inline theme script by hash: fail if they drifted apart.
py="$(command -v python3 || command -v python)"
"$py" scripts/check_csp.py public
