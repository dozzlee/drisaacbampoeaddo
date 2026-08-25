---
name: Dr Isaac Bampoe Addo Tribute
description: A solemn, resolute, and personal digital memorial.
colors:
  memorial-silver: "#d0d0d0"
  memorial-black: "#000000"
  raised-black: "#111111"
  soft-black: "#1c1c1c"
  ink: "#f4f4f4"
  quiet-ink: "#b8b8b8"
  white: "#ffffff"
  divider: "#343434"
typography:
  display:
    fontFamily: "Source Serif 4, Georgia, serif"
    fontSize: "clamp(2.55rem, 12vw, 5.25rem)"
    fontWeight: 600
    lineHeight: 1.12
    letterSpacing: "0.006em"
  headline:
    fontFamily: "Source Serif 4, Georgia, serif"
    fontSize: "clamp(2rem, 8vw, 3.8rem)"
    fontWeight: 700
    lineHeight: 1.12
  body:
    fontFamily: "Montserrat, Helvetica Neue, Arial, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.65
  label:
    fontFamily: "Montserrat, Helvetica Neue, Arial, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "0.14em"
rounded:
  surface: "12px"
  action: "0px"
spacing:
  xs: "8px"
  sm: "12px"
  md: "20px"
  lg: "32px"
  section: "88px"
components:
  button-primary:
    textColor: "{colors.white}"
    rounded: "{rounded.action}"
    padding: "14px 38px"
    height: "56px"
  button-ghost:
    textColor: "{colors.white}"
    rounded: "{rounded.action}"
    padding: "14px 38px"
    height: "56px"
  dark-panel:
    backgroundColor: "{colors.raised-black}"
    textColor: "{colors.white}"
    rounded: "{rounded.surface}"
    padding: "40px 24px"
---

# Design System: Dr Isaac Bampoe Addo Tribute

## Overview

**Creative North Star: "The Memorial Programme"**

The site should feel like a carefully prepared memorial programme enlarged into a digital environment: formal enough to honour public service, personal enough to hold a family memory, and quiet enough for the photographs to lead. Layered blacks create the ceremonial field, while silver and white keep the record readable.

The system rejects generic corporate landing-page polish, decorative funeral clichés, and busy image overlays. Precision comes from hairline dividers, measured type, purposeful image fades, and controls with clear physical edges.

**Key Characteristics:**

- Portrait-led compositions with protected text zones
- Black, charcoal, grey, silver, and white used with strong hierarchy
- Quarto-inspired Source Serif remembrance language paired with Montserrat records
- Flat, sharp outlined actions with centred uppercase labels
- Mobile layouts treated as primary compositions, not compressed desktop pages

## Colors

The palette is ceremonial and high-contrast. Several neutral shades of black create the classic funeral field, while silver, grey, and white provide hierarchy without introducing colour.

### Primary

- **Memorial Silver** (`#d0d0d0`): “In Loving Memory,” Share a Tribute outlines, timeline dates, active indicators, and the strongest moments of emphasis.
- Do not introduce red, pink, burgundy, rose, or any other chromatic accent.

### Neutral

- **Memorial Black** (`#000000`): Hero, header, timeline, mobile navigation, and footer fields.
- **Raised Black** (`#111111`): Primary content sections that separate from Memorial Black without relying on shadow.
- **Soft Black** (`#1c1c1c`): Tribute panels, captions, and interactive tonal states.
- **Ink** (`#f4f4f4`): Primary text across the black memorial field.
- **Quiet Ink** (`#b8b8b8`): Secondary text on dark surfaces, never used below readable contrast.
- **White** (`#ffffff`): Primary copy on dark fields and reading surfaces.
- **Divider** (`#343434`): Hairline structure between black surfaces.

**The Monochrome Signal Rule.** Silver marks remembrance, active state, or contribution. White is reserved for primary reading and strong hover inversions.

## Typography

**Display Font:** Source Serif 4 (with Georgia fallback), selected as a licensable Quarto-inspired alternative
**Body Font:** Montserrat (with Helvetica Neue and Arial fallbacks), matching the Bush 41 reference

**Character:** Source Serif 4 echoes the sturdy, open classical proportions of the Bush 41 site's commercial Quarto display face. Montserrat matches the reference site's body, navigation, and button typography while keeping dates, roles, and historical records clear.

### Hierarchy

- **Display** (600, `clamp(2.55rem, 12vw, 5.25rem)`, 1.12, `0.006em`): The honouree's name and no other repeated content. Its desktop cap matches the Bush 41 reference's measured 84px display size.
- **Headline** (700, `clamp(2rem, 8vw, 3.8rem)`, 1.12): Section titles and major legacy statements.
- **Title** (700, `1.1rem–1.3rem`, 1.2): Achievements, milestones, and contributor names.
- **Body** (400, `1rem`, 1.65): Narrative content, capped near 68 characters per line.
- **Label** (700, `0.75rem`, `0.14em`, uppercase): Short memorial and section labels only.

**The Name Has Space Rule.** Never place the full name over a detailed face on mobile. The portrait fades fully to Memorial Black before the display line begins.

## Elevation

The system is flat by default. Depth comes from tonal separation, image masks, borders, and overlap. Shadows are limited to the fixed header's small scroll-state cue; content panels do not float decoratively.

**The Structural Depth Rule.** Use a one-pixel divider or a clear tonal step before adding shadow.

## Components

### Buttons

- **Shape:** Sharp rectangular outline with square corners, a centred uppercase label, and no icon.
- **Primary:** Transparent field with a two-pixel Memorial Silver (`#d0d0d0`) outline and white label. Minimum height is `56px`.
- **Hover / Focus:** Solid white inversion and a three-pixel silver focus ring. No lift, gradient, shadow, or icon motion.
- **Secondary / Ghost:** Transparent white outline on dark fields, becoming solid white on hover.

### Cards / Containers

- **Corner Style:** Restrained `12px` radius.
- **Background:** Raised Black on dark fields; white or Soft White on reading surfaces.
- **Shadow Strategy:** None at rest.
- **Border:** One-pixel tonal dividers where grouping needs definition.
- **Internal Padding:** `24px` on mobile, up to `48px` for a single focused desktop panel.

### Navigation

Desktop navigation is a quiet Montserrat row on black with a silver underline response. Mobile navigation remains a full black field, uses larger Source Serif 4 links, a circular close control, and anchors the primary tribute action to the bottom.

### Portrait Slider

List every browser-compatible photograph in `js/pictures.js`, including photographs in nested folders, and generate a separate portrait-only list from their intrinsic dimensions. The hero begins with the designated final header, prioritizes all president-labelled photographs, and then continues through the remaining portrait list using two reusable image layers. President photographs remain eligible when landscape and use a full-image `contain` treatment so people are not cropped out. The lower gallery retains the complete archive. Expose previous and next header controls, and stop automatic movement for reduced-motion users. The image must fade to Memorial Black at its boundaries. Regenerate the manifest with `node scripts/generate-picture-manifest.mjs` whenever photographs are added or removed.

Use `headerfinal.png` as the opening hero image. After it, photographs whose filenames use president markers such as `pres`, `prez`, or `prezzy`, together with the known president photograph `oresz.jpg`, appear before the rest of the archive in both photo sequences. The Legacy portrait alternates every seven seconds between `F18_5598.JPG` and `F18_9952.JPG`, fading quietly between them without changing the surrounding card.

### Mobile Gallery

Preserve every gallery photograph's native aspect ratio below the desktop breakpoint. Landscape images remain wide and portrait images remain tall, with `object-fit: contain` preventing mobile crops. Desktop gallery tiles may use a consistent landscape frame for rhythm. In the mobile header only, portrait images use a centered `cover` crop so the image fills the frame without side edges; desktop portrait headers retain their reduced contained scale.

### Tribute Slider

One quotation occupies the reading area at a time. The panel uses Raised Black, a single quiet border, large serif quotation text, and 48px circular previous/next controls below on mobile.

## Do's and Don'ts

### Do:

- **Do** preserve the black-to-image fade at every viewport.
- **Do** maintain 44px minimum touch targets and visible keyboard focus.
- **Do** use flat, square outlined actions with centred labels for meaningful destinations.
- **Do** keep names, dates, achievements, quotations, and photographs clear and easy to navigate.
- **Do** let one decisive portrait lead the first screen.

### Don't:

- **Don't** make the site look like a generic corporate landing page or cheerful lifestyle brand.
- **Don't** use decorative funeral clichés.
- **Don't** place text over a visually busy face or allow disconnected image panels.
- **Don't** add ornamental effects that compete with the subject.
- **Don't** copy the SaaS subject matter from the supplied references; use their structural precision, control language, and responsiveness only.
