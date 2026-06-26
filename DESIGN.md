<!-- SEED: re-run $impeccable document once there's code to capture the actual tokens and components. -->

---
name: ChromaForge
description: Non-destructive photo color grading tool
---

# Design System: ChromaForge

## 1. Overview

**Creative North Star: "The Precision Darkroom"**

ChromaForge is a professional color grading tool — the interface should feel like a precision instrument, not a consumer app. Dark charcoal surfaces recede so the image dominates. Color is used sparingly and with purpose: a warm amber accent appears only where it signals interaction or state. The tool's personality is calm, dense, and confident — inspired by Lightroom Classic's functional density, DaVinci Resolve's hyper-professional dark surfaces, and Figma's clean inspector panels.

The system explicitly rejects clutter, decorative chrome, and anything that would distract from the image being graded. Every pixel of UI earns its place.

**Key Characteristics:**
- Dark, instrumental surfaces that put the image first
- Warm charcoal neutrals with an amber accent, used sparingly
- Dense information density without feeling crowded
- Responsive motion — feedback and transitions, no choreographed entrances
- Single sans-serif typeface throughout

## 2. Colors

**The Warm Charcoal Palette.** Dark warm-toned neutrals create an instrument-like atmosphere. A single amber accent provides interactive signaling without competing with the image content.

### Primary
- **Amber Accent** (`[to be resolved during implementation]`): Used exclusively for interactive elements — selected sliders, active toggles, hover states on interactive controls. Never decorative. Never as a background fill.

### Neutral
- **Deep Charcoal** (`[to be resolved during implementation]`): Primary surface background for panels and the main chrome. Warm-leaning (L 8–12%, slight hue toward amber at very low chroma).
- **Mid Charcoal** (`[to be resolved during implementation]`): Secondary surfaces — collapsible section headers, secondary panel backgrounds, toolbar backgrounds.
- **Warm Gray** (`[to be resolved during implementation]`): Text and labels. High contrast against deep charcoal (≥7:1 for WCAG AAA).
- **Muted Warm Gray** (`[to be resolved during implementation]`): Secondary text, metadata, disabled states.
- **Subtle Border** (`[to be resolved during implementation]`): Very subtle warm-tinted separators between panels, sections, and controls.

### Named Rules
**The Restrained Rule.** The amber accent is used on ≤5% of any given screen. Its rarity is the point — when the user sees amber, they know something is interactive or active.

**The Image-First Rule.** No surface color should compete with the image for visual attention. Avoid hues, gradients, or chroma in backgrounds that could skew the perceived color of the image being graded.

## 3. Typography

**Body Font:** Inter (with system sans-serif fallback)

ChromaForge uses a single sans-serif family throughout. Inter provides excellent legibility at small sizes (critical for dense slider labels and numeric readouts) while maintaining a precise, technical character that matches the tool's personality. No display face — hierarchy comes from weight and size contrast within the family.

### Hierarchy
- **Panel Title** (Inter Semi-Bold 600, 13px, 1.2): Section header labels in collapsible panels.
- **Slider Label** (Inter Medium 500, 12px, 1.2): Adjustment parameter names next to sliders.
- **Value Readout** (Inter Regular 400, 12px, 1.2): Numeric slider values, editable inline.
- **Body/Labels** (Inter Regular 400, 11px, 1.3): Sub-labels, tabs, secondary metadata. Upper limit 65–75ch for any prose.
- **Mono Numeric** (Inter Regular 400, same sizes): For histogram readouts and precise value entry — Inter's tabular figures handle this naturally.

### Named Rules
**The Single Voice Rule.** One typeface, across the entire UI. No display face, no mono face. Weight and size do the work of hierarchy.

## 4. Elevation

Flat by default. Surfaces are distinguished by tonal layering (lighter charcoals on darker charcoals) rather than shadows. Minimal shadow use — a subtle drop shadow only for floating elements (popovers, dropdowns, tooltips) that need separation from the panel stack. The tool is a single-plane darkroom, not a layered card interface.

## 5. Components

*No components exist yet. Seed placeholder — real tokens and patterns to be captured on next `$impeccable document` pass once code exists.*

## 6. Do's and Don'ts

### Do:
- **Do** use the amber accent only for interactive elements and active states.
- **Do** use tonal layering (lighter charcoal on deep charcoal) for surface hierarchy.
- **Do** keep the image canvas free of any chrome or UI overlay beyond the histogram.
- **Do** use Inter throughout — weight contrast is your hierarchy tool.

### Don't:
- **Don't** build a UI that looks like GIMP or overly complex toolbars — "no bloat" means every visible element earns its place, and no element exists without a clear job.
- **Don't** use color decoratively (gradients, colored panel backgrounds, chroma-filled surfaces).
- **Don't** use shadows as a default surface treatment — reserve them for floating elements only.
- **Don't** introduce a second typeface — the single-family hierarchy is deliberate.
- **Don't** use border-left or border-right accents on panels; use full background tinting instead.
