# Product

## Register

product

## Users

Photographers and color graders — from serious enthusiasts to working professionals — using desktop workstations (Windows/Linux) for photo editing. Their context: sitting at a desk, focused on one image at a time, making precise tonal and color decisions. The primary task is adjusting global image parameters with real-time visual feedback while monitoring a live histogram.

## Product Purpose

A professional-grade, non-destructive photo color grading tool for Windows and Linux. Focused on doing global tonal/color adjustments extremely well — no bloat, no subscription, no catalog/library management. The original image file is never modified; every edit is parametric and stored in a sidecar. Success means a user can import a RAW or compressed image, apply any combination of global adjustments with real-time preview, undo/redo freely, and export a fully-processed result with the source file untouched.

## Brand Personality

Precise, pro, uncluttered.

- Voice: direct and knowledgeable, not hype-driven. Technical where appropriate, never marketing-buzzy.
- Tone: calm confidence. The tool assumes the user knows what they're doing and gets out of their way.
- Emotional goal: the user feels in control, not entertained. The interface is a precise instrument, not a personality.

## Anti-references

- Overly complex or cluttered UIs (GIMP, old Photoshop with every toolbar visible). "No bloat" means every visible element earns its place.
- Cheap consumer photo apps with basic sliders and phone-filter aesthetics.
- Generic SaaS startup look: bright colors, oversized rounded everything, cartoon icons.

## Design Principles

1. **Dark by default, instrumental by nature.** The interface recedes so the image dominates. Dark theme is not an aesthetic choice — it prevents the UI from skewing perceived color/contrast of the image being graded.
2. **Every pixel of UI earns its place.** No decorative elements, no badges, no chrome that isn't interactive or informational. A slider with a label and value is enough.
3. **Real-time feedback is a hard requirement.** The preview must track slider movement at interactive framerates. The processing pipeline runs on a worker thread; the UI never freezes.
4. **Consistency over cleverness.** All adjustments follow a fixed pipeline order. All sliders behave identically (drag, numeric input, double-click reset). The user builds muscle memory once.
5. **The original file is sacred.** Non-destructive is not a feature — it's a constraint baked into every architectural decision.

## Accessibility & Inclusion

WCAG AAA target. Minimum 7:1 contrast for body text, 4.5:1 for large text. Full keyboard navigation for all controls. Reduced motion alternative for any animation. Color-vision-safe choices for indicators that rely on hue.
