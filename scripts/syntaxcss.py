"""Build assets/css/syntax.css from two Chroma styles: a light one and a dark one.

Token colours are nudged until they reach WCAG AA (4.6:1) against the site's code
background, backgrounds are dropped (the site paints its own), and the dark style
is scoped to the site's dark-mode selectors."""
import colorsys
import re
import subprocess
import sys

LIGHT_BG = "#fffdf9"
DARK_BG = "#1a1c20"
TARGET = 4.6


def lum(hex6):
    r, g, b = (int(hex6[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def expand(c):
    c = c.lower()
    return "#" + "".join(ch * 2 for ch in c[1:]) if len(c) == 4 else c


def fix(color, bg):
    color = expand(color)
    if ratio(color, bg) >= TARGET:
        return color
    r, g, b = (int(color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    step = -0.01 if lum(bg) > 0.5 else 0.01
    while 0 <= l <= 1:
        l += step
        rr, gg, bb = colorsys.hls_to_rgb(h, min(max(l, 0), 1), s)
        cand = "#%02x%02x%02x" % (round(rr * 255), round(gg * 255), round(bb * 255))
        if ratio(cand, bg) >= TARGET:
            return cand
    return "#000000" if step < 0 else "#ffffff"


def rules(style, bg, scope):
    css = subprocess.run(["hugo", "gen", "chromastyles", f"--style={style}"], capture_output=True, text=True, check=True).stdout
    out = []
    for comment, selector, body in re.findall(r"/\*\s*(.*?)\s*\*/\s*([^{]+)\{([^}]*)\}", css):
        selector = selector.strip()
        if not selector.startswith(".chroma ."):
            continue
        cls = selector[len(".chroma "):]
        if cls in (".lntd", ".lntable", ".hl", ".lnt", ".ln", ".line", ".cl", ".lnlinks"):
            continue
        decls = []
        for prop, val in re.findall(r"([a-z-]+)\s*:\s*([^;]+);?", body):
            val = val.strip()
            if prop == "color" and val.startswith("#"):
                decls.append(f"color:{fix(val, bg)}")
            elif prop in ("font-weight", "font-style", "text-decoration"):
                decls.append(f"{prop}:{val}")
        if decls:
            sels = ",".join(f"{s} .chroma {cls}" for s in scope)
            out.append(f"{sels}{{{';'.join(decls)}}} /* {comment} */")
    return out


def main(light, dark, dest):
    lines = [f"/* Code highlighting: Chroma '{light}' (light) and '{dark}' (dark), colours adjusted to WCAG AA. Generated, do not edit. */"]
    lines += rules(light, LIGHT_BG, [""])
    lines.append("@media (prefers-color-scheme: dark) {")
    lines += ["  " + r for r in rules(dark, DARK_BG, [':root:not([data-theme="light"])'])]
    lines.append("}")
    lines += rules(dark, DARK_BG, [':root[data-theme="dark"]'])
    open(dest, "w", encoding="utf-8", newline="\n").write("\n".join(l.replace(" .chroma", ".chroma", 1) if l.startswith(" .chroma") else l for l in lines) + "\n")
    print(f"wrote {dest}: {len(lines)} lines")


if __name__ == "__main__":
    main(*sys.argv[1:4])
