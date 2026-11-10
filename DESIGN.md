---
version: 1
colors:
  canvas: "#100d0c"
  surface: "#ffffff"
  surfaceRaised: "#ecebed"
  line: "#dedddd"
  text: "#171514"
  muted: "#6b6866"
  accent: "#ff5000"
  warning: "#f3c56a"
typography:
  display:
    fontFamily: "Georgia, Times New Roman, serif"
  body:
    fontFamily: "DM Sans, system-ui, sans-serif"
  utility:
    fontFamily: "DM Sans, system-ui, sans-serif"
rounded:
  panel: "28px"
  card: "20px"
  control: "14px"
  pill: "999px"
spacing:
  unit: "4px"
components:
  panel:
    background: "#ffffff"
    border: "#dedddd"
  primaryButton:
    background: "#ff5000"
    foreground: "#ffffff"
---

## Visual system

Use a dark Phoenix night scene, a moonlit dinner foreground, white panels, orange actions, and neutral controls. Georgia owns the hero headline; DM Sans owns interface text. Runtime tokens live in `apps/frontend/src/styles.css` and `apps/frontend/src/shadcn.css`.

## Layout

Desktop uses a 30/70 hero and panel split inside the viewport. The planner fits without document scrolling. Result tabs share a consistent panel size; long content scrolls within the panel. Mobile stacks the hero and panel with natural document scrolling.

The background is `public/images/phoenix-night-layer.png`. The transparent foreground is `public/images/phoenix-dinner-night-layer.png`. Keep these separate to preserve depth.

## Components

Use the shared shadcn/Radix components for fields, selects, calendars, tabs, popovers, and dialogs. The cactus/fork logo uses the white SVG on dark surfaces and the black SVG on light surfaces. Keep its aspect ratio intact.

The itinerary has numbered venue cards and a summary sidebar. The map uses dark Google styling, selectable stop markers, and actual route geometry. Details keeps the selected venue while switching tabs and displays only supported venue facts.

## States

Use inline errors and local retry actions. Keep controls and panel dimensions stable during loading. Distinguish verified, provisional, and unresolved results. Use a neutral placeholder for unavailable venue photos. Never substitute unrelated imagery or draw straight lines as road routes.

Preserve provider attribution, visible keyboard focus, reduced-motion support, and usable scrollbars. New styles should extend shared components rather than add competing screen-specific variants.
