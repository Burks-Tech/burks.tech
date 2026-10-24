"""Fail the build if any inline script in the generated HTML is not allowed by the CSP in _headers."""
import base64
import hashlib
import pathlib
import re
import sys

INLINE_SCRIPT = re.compile(r"<script(?![^>]*\bsrc=)(?![^>]*ld\+json)[^>]*>(.*?)</script>", re.S)


def main(root):
    root = pathlib.Path(root)
    csp = re.search(r"Content-Security-Policy: (.+)", (root / "_headers").read_text(encoding="utf-8"))
    if not csp:
        sys.exit("check_csp: no Content-Security-Policy in _headers")
    allowed = set(re.findall(r"'(sha256-[A-Za-z0-9+/=]+)'", csp.group(1)))
    pages, problems = 0, []
    for page in sorted(root.rglob("*.html")):
        pages += 1
        for body in INLINE_SCRIPT.findall(page.read_text(encoding="utf-8")):
            digest = "sha256-" + base64.b64encode(hashlib.sha256(body.encode("utf-8")).digest()).decode()
            if digest not in allowed:
                problems.append(f"{page.relative_to(root)}: inline script {digest} not in CSP")
    if problems:
        sys.exit("check_csp: " + "\n".join(problems))
    print(f"check_csp: {pages} pages, every inline script allowed by the CSP")


if __name__ == "__main__":
    main(sys.argv[1])
