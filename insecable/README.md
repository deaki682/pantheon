# Insécable — French typography fixer (MV3 Chrome extension)

One job: insert the correct **French non-breaking spaces** (narrow `U+202F` before
`; ! ?`, full `U+00A0` before `:`, and inside `« »`) and fix quotes, on the text
you just typed or selected — the fiddly stuff translators currently do by hand or
with an AutoHotkey script. **100% local. No account, no network, no per-user cost.**

## Why this exists

The generic "smart quotes / dashes" niche is already free and saturated. The one
thing no in-browser tool automates is the French NBSP-before-punctuation rule, and
the pain is loud (see the ProZ threads). That — French only — is the whole product.

## How it works (the whole thing, in one screen)

- **`engine.js`** — the entire product. A pure `fixText(text, settings)` with three
  guarantees: **idempotent** (running twice == once), **safe** (masks URLs, emails,
  code, emoticons, times like `12:30`, and primes like `6'2"` before touching
  anything), and **fr-FR only**. Runs unchanged in the popup, injected into pages,
  and under Node for tests.
- **`background.js`** — the service worker. A context-menu item and a keyboard
  command (`Ctrl/Cmd+Shift+F`) inject `engine.js` into the current tab, run the fix
  on the focused field / selection, and write it back with `execCommand('insertText')`
  so **native undo is preserved**.
- **`popup.html/js`** — a paste box that runs the same engine. This path works
  **everywhere** (including where in-field editing can't reach), and is the
  10-second demo: paste, see it fixed live, copy.
- **`options.html/js`** — the one real choice (space mode) plus per-rule toggles.

## Honest reach limits

In-field correction works in `<textarea>`, `<input>`, and most `contenteditable`
fields (email, many CMS, forums, web editors). It **does not work in Google Docs**
(canvas renderer — there is no text node to touch) and is unreliable in some
framework rich-editors (Slate/ProseMirror/Quill). For those, use the popup paste box.

## The one setting

`U+202F` (narrow, default) is what French QA tools expect but can render invisibly
on some Apple/Safari setups; the **compatibility** toggle switches everything to the
always-visible `U+00A0`. The colon always takes `U+00A0` (Imprimerie nationale).

## Develop

```bash
node test/engine.test.js     # 34 assertions: rules, safety guards, idempotency
node tools/make-icons.js     # regenerate icons/ (no dependencies)
```

Load unpacked: `chrome://extensions` → Developer mode → *Load unpacked* → this folder.
Then verify: focus any textarea, type `"Bonjour!"`, press `Ctrl+Shift+F` → `« Bonjour ! »`.

No build step. No dependencies. Meant to be fully re-readable in one sitting.
