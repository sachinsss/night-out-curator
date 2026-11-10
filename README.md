<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="apps/frontend/public/images/nightline-food-cactus-white.svg" />
    <img src="apps/frontend/public/images/nightline-food-cactus-black.svg" width="64" height="64" alt="Night-Out Curator logo" />
  </picture>
</p>

<h1 align="center">Night-Out Curator</h1>

<p align="center">
  Plan a Phoenix night out around your food preferences, budget, group, and travel plans.
  Get an ordered itinerary with venue details, photos when available, and Google Maps routes.
</p>

<p align="center">
  <a href="#website-preview">Website Preview</a> ·
  <a href="#features">Features</a> ·
  <a href="#install--run">Run Locally</a>
</p>

<p align="center">
  <a href="https://react.dev/"><img src="https://img.shields.io/badge/React-20232a?logo=react&logoColor=61dafb" alt="React" /></a>
  <a href="https://www.typescriptlang.org/"><img src="https://img.shields.io/badge/TypeScript-3178c6?logo=typescript&logoColor=white" alt="TypeScript" /></a>
  <a href="https://vite.dev/"><img src="https://img.shields.io/badge/Vite-646cff?logo=vite&logoColor=white" alt="Vite" /></a>
  <a href="https://nodejs.org/"><img src="https://img.shields.io/badge/Node.js-339933?logo=nodedotjs&logoColor=white" alt="Node.js" /></a>
  <a href="https://www.sqlite.org/"><img src="https://img.shields.io/badge/SQLite-003b57?logo=sqlite&logoColor=white" alt="SQLite" /></a>
</p>

## Website Preview

### Night planner

![Night-Out Curator planner with a Phoenix night scene, dinner foreground, and itinerary preferences](docs/images/planner.png)

## Features

- **Plan around your evening** — choose a location, date, start time, party size, budget, stops, and transportation.
- **Set your preferences** — pick cuisines, mood, dietary requirements, excluded categories, and additional notes.
- **Choose a starting point** — enter a location, use your current position, or select a point on the map.
- **Review your itinerary** — browse numbered stops, ratings, scheduled times, and estimated costs.
- **Explore the route** — view selectable stop markers and Google road or transit geometry.
- **Check venue details** — see available photos, addresses, planning information, and website or review links.
- **Edit without losing results** — keep your draft and return to the last generated itinerary without regenerating it.

Unavailable provider data stays unavailable. Photos use a neutral placeholder when none are returned, and incomplete travel verification is shown as provisional.

## Tech Stack

| Layer                  | Technologies                                             |
| ---------------------- | -------------------------------------------------------- |
| Frontend               | React, TypeScript, Vite                                  |
| Components and styling | shadcn/ui, Radix UI, Tailwind CSS, Lucide                |
| Backend                | Node.js, Fastify                                         |
| Validation             | Zod and shared TypeScript contracts                      |
| Planning               | AI SDK with discovery and planning agents                |
| Places and routes      | Google Maps JavaScript API, Places API (New), Routes API |
| Persistence            | Node's built-in SQLite and an in-memory LRU cache        |
| Testing and formatting | Vitest, Testing Library, Prettier                        |

## Resources Used

### Libraries & Tools

- [React](https://react.dev/), [Vite](https://vite.dev/), and [TypeScript](https://www.typescriptlang.org/) — application UI and tooling.
- [shadcn/ui](https://ui.shadcn.com/), [Radix UI](https://www.radix-ui.com/), and [Tailwind CSS](https://tailwindcss.com/) — accessible components and styling.
- [Lucide](https://lucide.dev/) — interface icons.
- [Fastify](https://fastify.dev/) and [Zod](https://zod.dev/) — API routing and validation.
- [AI SDK](https://ai-sdk.dev/) — structured model calls through configurable providers.
- [Google Maps Platform](https://developers.google.com/maps) — location lookup, venue information, photos, weather, and routes.
- [Vitest](https://vitest.dev/) and [Testing Library](https://testing-library.com/) — automated tests.

### Images & Attribution

- The project screenshot is stored in [`docs/images`](docs/images).
- The logo and night-scene layers are stored in [`apps/frontend/public/images`](apps/frontend/public/images).
- Venue photos and map content come from Google Maps when available. Provider and photographer attribution remain visible in the app.

## Install & Run

Use **Node.js 24** and npm. SQLite runs inside Node; no separate SQL server is required.

Install dependencies and create a local environment file:

```powershell
npm.cmd ci
Copy-Item .env.example .env
```

Fill in the root `.env`:

| Variable                   | Value                                                                    |
| -------------------------- | ------------------------------------------------------------------------ |
| `LLM_PROVIDER`             | `openai`, `anthropic`, `google`, or `openai-compatible`                  |
| `LLM_MODEL`                | A model available from your provider                                     |
| `LLM_API_KEY`              | Your server-side model key                                               |
| `LLM_BASE_URL`             | Required for `openai-compatible`; optional otherwise                     |
| `GOOGLE_MAPS_API_KEY`      | Server key for Places, Photos, Routes, Geocoding, and Weather            |
| `VITE_GOOGLE_MAPS_API_KEY` | Browser key restricted to Maps JavaScript API and your website referrers |

Provider-specific keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY`) can be used when `LLM_API_KEY` is unset. The `DISCOVERY_LLM_*` and `PLANNING_LLM_*` variables optionally override the shared model settings.

Allow these local referrers on the browser key:

```text
http://localhost:5173/*
http://127.0.0.1:5173/*
```

Start the application:

```powershell
npm.cmd run dev
```

- **Frontend:** http://localhost:5173/
- **Backend health:** http://127.0.0.1:3000/api/v1/health

Restart the relevant service after changing `.env`. Keep server credentials out of browser configuration and never commit `.env`.

### Development Commands

```powershell
npm.cmd run typecheck
npm.cmd test
npm.cmd run build
npm.cmd run format:check
```

Use `npm.cmd run format` to format source and documentation. Backend logs appear in its terminal. If port 3000 is occupied, check the health endpoint before starting another backend instance.

### Project Structure

```text
apps/
  frontend/       React planner and result views
  backend/        Fastify API, agents, integrations, and SQLite
packages/
  contracts/      Shared request and response schemas
docs/
  images/         README screenshots
```

See [API examples](docs/api-testing.md) and [design conventions](DESIGN.md) for implementation details.

## Connect With Me

[GitHub](https://github.com/SushanthOO7) · [Portfolio](https://sushanth.tech)

---

<p align="center">Built by Sushanth U V.</p>
