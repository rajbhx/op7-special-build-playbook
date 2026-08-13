# 11 — True-black (AMOLED) theming for Fenix/GeckoView forks

Reusable playbook for making a Fenix-family browser (Iceraven/Firefox/derivatives)
render **pure black** on AMOLED panels without breaking structure, plus a
device-brand accent (OnePlus red example). Proven on Iceraven OP7 r5→r7.

## 1. Know the token hierarchy (night theme)

`app/src/main/res/values-night/colors.xml` is the single source for dark mode:

- Material3 tokens: `fx_mobile_background`, `fx_mobile_surface`,
  `fx_mobile_surface_container[_low/_lowest/_high/_highest]`, `surface_bright`,
  `surface_dim`, `surface_variant`, `outline`, `outline_variant`.
- Legacy layer tokens: `fx_mobile_layer_color_2` (cards/menus/dialogs),
  `fx_mobile_layer_color_3` (search), `fx_mobile_splashscreen_background`.
- Dark-mode accent family: `accent_normal_theme`, `accent_high_contrast_normal_theme`,
  `fill_link_from_clipboard_normal_theme`, `prompt_login_edit_text_cursor_color_normal_theme`.

Map every UI surface back to one of these tokens before editing anything.
Compose sub-screens read the Material3 `colorSurfaceContainer*` tokens; XML
screens read `fx_mobile_layer_color_2`; the splash reads its own token.

## 2. Pure-black recipe (what r7 does)

- Remap ALL of: background, surface, dim, surface_variant, surface_bright,
  every `surface_container*`, `layer_color_2`, `layer_color_3`, splash →
  `#FF000000`. No gray fills survive.
- Carry structure with **hairlines, not lit fills**:
  - `fx_mobile_outline` = `#FF2A2A2A`, `fx_mobile_outline_variant` = `#FF242424`.
  - Cards that must remain visible get a 1dp stroke of `#FF242424` around a
    pure-black fill (`<stroke android:width="1dp" .../>` in the shape).
- Keep `fx_mobile_on_surface` near-white (`#f2f0f8` ≈ 18.6:1 on black) — text
  contrast is the only thing that must never regress.
- Splash: `#210340` purple → `#000000` for an instant-black AMOLED launch
  (combine with the seamless-launch trick: splash = surface color).

## 3. The androidx.preference trap (settings page goes void)

- `PreferenceFragmentCompat` rows are **transparent ripples** over the activity
  `colorBackground`; `Preference` has no `android:background`.
- Its list divider is `#1f000000` — invisible on black. Raising container tokens
  alone does NOT fix the main settings list.
- Fix at the source (r6, kept in r7):
  1. New `@layout/op7_preference_row.xml` = pinned copy of androidx.preference
     1.2.1 `preference_material` (same child structure, root gets card bg +
     insets). Wire via `PreferenceTheme.preferenceStyle` and
     `SwitchCompatPreferenceMaterialStyle` (`android:layout`).
  2. New `@drawable/op7_preference_row_background.xml` = ripple + rounded shape;
     r7: fill `?attr/colorSurfaceContainer` (black) + 1dp `#242424` stroke.
  3. Neutralize `preference_list_divider_material.xml` (drawable + drawable-v21)
     → transparent.
- Pinning a library layout is intentional: an upstream androidx bump that changes
  the layout will surface as a patch conflict and STOP the pipeline (by design).

## 4. Brand accent without losing privacy identity

OnePlus red example (patch 006):

- Night: `fx_mobile_primary` = `#FFEB0029`, `primary_container` = `#FF4D000F`,
  `primary_inverse` = `#FFFF3346`, `accent_normal_theme` = `#FFEB0029`,
  high-contrast = `#FFFF3346`.
- Day: `primary` = `#FFEB0029`, `primary_container` = `#FFFFD9DE`,
  `primary_inverse` = `#FFFF4D5E`.
- Contrast check: `#EB0029` on `#000000` ≈ 4.6:1 → AA for normal-size accent
  text; keep `on_primary` near-white.
- **Do NOT recolor private-mode identity**: `fx_mobile_icon_color_accent_violet`,
  private dashboard colors stay violet so private browsing stays visually distinct.
- Day `accent_normal_theme` = `photonInk20` is TEXT color in light mode, not a
  brand accent — leave it alone.

## 5. Patch generation that never lies (real blob hashes)

Hand-assembled `index` lines in patches rot (r5 bug: wrong before-hash). Always:

1. Fetch the pristine upstream files (raw.githubusercontent at the pinned SHA).
2. `git init` a scratch repo, commit the pristine files as "upstream baseline".
3. Apply edits, `git add -A`, commit as "patch N".
4. `git show --format= --binary <commit>` → real diffs with true blob hashes.
5. Verify on a SECOND fresh repo: `git apply --check` each patch in order,
   `git apply`, then `diff -r` the result against the target tree — must be
   byte-identical.
6. When two patches touch the same file (e.g. 005 + 006 both edit
   `values-night/colors.xml`), keep hunks in non-overlapping line ranges and
   prove the sequence applies 005→006 on pristine.

## 6. Measurement (does pure black actually save power?)

- Black-pixel coverage: screenshot the same screens (home, settings, menus) and
  count pixels with luminance 0 vs <64 (r5 baseline: ~10% pure black → target
  ~100% on chrome).
- Screen-on drain: `dumpsys batterystats` before/after, same brightness, idle UI.
- Rule: revert if a theme change damages text contrast, readability, or any
  benchmark; cosmetic-only patches must never touch security/process behavior.
