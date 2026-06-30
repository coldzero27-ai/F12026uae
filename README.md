# F1 2026 World Calendar Globe

An interactive 3D globe dashboard for the 2026 Formula 1 season, built as a single self-contained HTML file for a wall display (designed for a 65" TV at 16:9). Race countries glow on the globe; click one to see that round's details floating in space. Driver and constructor standings, the full season schedule, and a live countdown sit around the edges. All session times are converted to UAE time (GST, UTC+4).

## Live demo

Once published with GitHub Pages (see below), the dashboard is the site root — just open the Pages URL.

## Files

- **index.html** — the entire dashboard. Self-contained: 3D globe, coastline data, background image, schedule, and all logic are embedded. No build step, no dependencies to install.
- **.nojekyll** — tells GitHub Pages to serve files as-is (recommended for static sites).

The only thing loaded from the internet at runtime is the three.js library (from a CDN) and the live F1 data (see below).

## What updates automatically

- **Race status** (done / next / upcoming) and the **countdown** are computed from the current date in the browser. No maintenance.
- **Session times** (Practice / Qualifying / Sprint / Race) are fetched live from the Jolpica F1 API and converted to UAE time, with correct date rollovers.
- **Driver and constructor standings** and **race results / podiums** are fetched live from Jolpica on load.

The season schedule, circuits, dates, and locations are baked in as a verified fallback, so the globe and calendar still work if the network or API is unavailable. When that happens, the standings panels show "unavailable" rather than breaking.

Data source: [Jolpica F1 API](https://github.com/jolpica/jolpica-f1) (`https://api.jolpi.ca/ergast/f1/2026`), the community-maintained successor to the Ergast API — free, no authentication. It's run by volunteers and rate-limited, so live panels may occasionally be empty; a page refresh usually fixes it.

Schedule verified against the official Formula 1 2026 calendar.

## Controls

Move the mouse to the top of the screen to reveal the control bar:

- **Dot grid / Continent fill** — globe surface style
- **Navy / F1 blue / Earth** — ocean colour
- **Dark / Light** — theme (dark uses the space background; light is a daytime design)
- **Fit** — rescale to the window
- **Present** — fullscreen

On the globe: drag to rotate, scroll to zoom, hover a marker for the Grand Prix name, click a marker (or a row in the schedule list) to open its floating card. Click empty space to dismiss.

## Publishing to GitHub Pages

1. Create a new repository on GitHub (e.g. `f1-2026-globe`).
2. Upload `index.html` and `.nojekyll` to the repository root.
3. In the repo, go to **Settings → Pages**.
4. Under **Build and deployment**, set **Source** to *Deploy from a branch*, branch `main` (or `master`), folder `/ (root)`.
5. Save. After a minute or two, your dashboard is live at `https://<your-username>.github.io/<repo-name>/`.

To put it on the TV, open that URL in the TV's browser and use the **Present** button for fullscreen.

## Notes

- The F1 logo and race cars are part of the background image. The official F1 logo is a trademark; this project is for personal, non-commercial display.
- The globe coastlines use public-domain Natural Earth 1:50m data, simplified for size.
- If the live session times or standings ever stop loading, it's almost always the Jolpica API being rate-limited or temporarily down — the rest of the dashboard keeps working.
