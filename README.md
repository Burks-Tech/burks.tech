# burks.tech

The source of [blog.burks.tech](https://blog.burks.tech): a [Hugo](https://gohugo.io/) site with a hand-written theme, built and served by Cloudflare Workers. No JavaScript framework, no third-party requests, no cookies.

## Write a post

1. Create it: `hugo new content posts/<slug>/index.md`. This makes a draft from `archetypes/posts.md`. The folder name is the URL: `/posts/<slug>/`, and it never changes once published.
2. Write Markdown in `index.md`. Images go in the same folder and are resized automatically. GitHub-style callouts (`> [!NOTE]`, `> [!WARNING]`) work. For a post that summarises a repository, fill in `source` and optionally `stats` in the front matter; the post then gets the title block, the stat strip and a link card to the repository.
3. Preview it: `hugo server -D`, then open <http://localhost:1313>.
4. Remove `draft: true`, commit, push a branch and open a pull request. Cloudflare builds every branch, drafts included, and posts a preview link on the pull request.
5. Merge to `main`. The site is live about a minute later.

To update a published post, edit it and add `lastmod: YYYY-MM-DD` to the front matter; the title block then shows the update date.

Link to other pages on the site by path, for example `[the migration](/posts/cephadm-to-rook-in-place/)`. The build fails if such a link does not resolve, so a typo never ships.

## Build

```sh
./build.sh
```

`build.sh` checks the Hugo version (`HUGO_VERSION`, default `0.168.0`), builds into `public/` with drafts only on branches other than `main`, then checks that the Content Security Policy allows every inline script. You need Hugo extended 0.168.0 (`winget install Hugo.Hugo.Extended --version 0.168.0`, or `brew install hugo`) and Python 3.

## Deploy

Cloudflare Workers static assets, connected to this repository with Workers Builds:

| Setting | Value |
|---|---|
| Worker name | `burks-tech` (from `wrangler.jsonc`) |
| Build command | `./build.sh` |
| Deploy command | `npx wrangler deploy` |
| Preview command (other branches) | the default, `npx wrangler preview` |
| Build variable | `HUGO_VERSION` = `0.168.0` |
| Custom domain | `blog.burks.tech` (Worker > Settings > Domains & Routes) |
| Apex | `burks.tech` redirects to `https://blog.burks.tech` with a Cloudflare redirect rule on the zone |

`wrangler.jsonc` serves `public/` with no Worker script. `public/_headers` is generated from `layouts/home.headers` and sets the security headers and long cache lifetimes for fingerprinted assets.

To upgrade Hugo, change `HUGO_VERSION` in the Cloudflare build variables, the default in `build.sh` and `module.hugoVersion.min` in `hugo.toml` together.

Cloudflare Web Analytics is switched on by putting the site token (public, it ships in every page) in `params.cfBeaconToken` in `hugo.toml`; the CSP allows the beacon only when the token is set.

## Layout

```
archetypes/      front matter template for new posts
assets/css/      main.css (the theme) and syntax.css (generated)
assets/js/       theme-init.js (inline, pre-paint) and main.js (theme toggle, copy buttons)
assets/og/       share-card background and the fonts used to draw on it
content/         pages and posts
data/            projects.yaml, the project cards
layouts/         the theme: templates, partials, render hooks, RSS, _headers
scripts/         build check and asset generators
static/          favicons and web fonts
```

## Regenerating assets

- Code highlighting colours: `python scripts/syntaxcss.py rose-pine-dawn dracula assets/css/syntax.css`. Token colours are adjusted until they pass WCAG AA against the code background.
- Favicon, touch icon and share-card background: `python scripts/brandart.py . assets/og` (needs Pillow).

## Licence

Writing is CC BY 4.0, code is MIT, fonts are SIL OFL 1.1. See [LICENSE.md](LICENSE.md).
