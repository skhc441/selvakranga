# Personal site — Selva Kumar Ranganathan

A single-page static site. No build step, no dependencies: three files plus an
assets folder.

```
index.html    all content and page structure
styles.css    design tokens + all styling (dark and light themes)
script.js     theme toggle, mobile menu, scroll reveal, counters, hero canvas
assets/       put portrait.jpg here (square) and it appears automatically
serve.py      local preview server
tools/        make_portrait.py — crops any image to assets/portrait.jpg
```

## Preview locally

```bash
python3 serve.py
```

Then open <http://127.0.0.1:4173/>. Pass a different port as an argument if 4173
is taken. Opening `index.html` directly with `file://` also works in most
browsers, but the local server is closer to how it will behave when deployed.

## Editing

Content lives in `index.html` — plain HTML, no templating. Each section is
marked with a comment banner (`HERO`, `ABOUT`, `WORK`, `RESEARCH`, …).

Colours, spacing and fonts are CSS custom properties at the top of `styles.css`,
under `:root` for dark and `:root[data-theme="light"]` for light. Changing
`--accent` in both blocks re-themes the whole site.

To add a scroll-in animation to a new element, give it `class="reveal"`; to
stagger it after its neighbours, add `style="--d:.06s"`.

## The portrait

The about block shows an "SR" monogram rather than a photo, by choice.

To use a photo instead: put a square image at `assets/portrait.jpg`, then in
`index.html` remove the `no-photo` class from `<div class="portrait no-photo">`
and add an image tag inside it pointing at that file. `tools/make_portrait.py`
will crop any source image to the right shape:

```bash
python3 tools/make_portrait.py ~/path/to/photo.jpg
```

It trims uniform borders, crops square biased toward the top of the frame where
faces sit, and writes `assets/portrait.jpg`. Use `--bias 0.5` to centre the
crop, `--size 1200` for a larger file, or `--rect x,y,w,h` to aim at an exact
region of the source. It needs only `sips`, which ships with macOS.

## Still to fill in

The Google Scholar metrics in the hero and the Research section (9 publications,
63 citations, h-index 5, i10-index 3) are hard-coded. Refresh them from the
profile when they move.

## Deploying

The site is live at <https://skhc441.github.io/selvakranga/>, served by GitHub
Pages from the `main` branch of `skhc441/selvakranga`. Deploying is just:

```bash
git add -A && git commit -m "your message" && git push
```

Pages rebuilds in about 30 seconds.

GitHub Pages sends `Cache-Control: max-age=600`, so browsers hold onto
`styles.css` and `script.js` for ten minutes. If you change either and want the
update to appear immediately, bump the `?v=` number on both links in
`index.html` — they are next to each other near the top and bottom of the file.

`CLAUDE.md` and `assets/source/` are deliberately **not** in the repo (see
`.gitignore`); they stay local and travel between machines through OneDrive.

### Other hosts

Any static host works, since there is nothing to build. Upload the folder, or
point GitHub Pages / Netlify / Cloudflare Pages at the repository root.

The contact form opens the visitor's email client via `mailto:` — it needs no
backend. To collect submissions server-side instead, point the form at a service
like Formspree and remove the submit handler at the bottom of `script.js`.
