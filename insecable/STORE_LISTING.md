# Chrome Web Store listing — Insécable

## Name (ranks for the function keywords, impersonates nothing)
**Insécable — typographie française**

Rationale: translators search "espace insécable", "typographie française", "guillemets
français", "espace avant point d'interrogation". "Insécable" (= non-breaking) owns the
concept without copying any existing brand (Smart Typography, SmartType, Antidote,
ModHeader, etc.).

## Short description (132 char max)
> Corrige les espaces insécables français (avant ; ! ? : et dans « ») et les guillemets, dans votre champ de saisie. 100 % local.

## Category / language
Productivity · Primary language: French

## Full description

**Les espaces insécables français, enfin automatiques — directement dans votre navigateur.**

Vous traduisez ou rédigez en français dans un outil web (TAO en ligne, post-édition,
Google Docs, CMS, e-mail) ? Insécable insère les bons espaces là où la typographie
française l'exige, en une action :

• espace fine insécable **U+202F** avant `;` `!` `?`
• espace insécable **U+00A0** avant `:` (règle de l'Imprimerie nationale)
• guillemets français **« … »** avec l'espace intérieur correct
• apostrophe typographique `'` → `'`, points de suspension `…`, tiret cadratin
• symboles : `20 %`, `12,50 €`, `14 h 30`

**Comment ça marche**
1. Dans un champ de texte : sélectionnez (ou non) votre texte, puis clic droit →
   « Corriger la typographie française », ou raccourci **Ctrl/Cmd + Maj + F ».
2. Partout ailleurs : ouvrez la fenêtre de l'extension, collez, corrigez, copiez.

**Sûr par conception**
Insécable ne touche jamais à vos URL, e-mails, code, émoticônes `:)`, heures `12:30`
ni aux mesures `6'2"`. Il est idempotent (le relancer ne change rien de plus). Et il
fonctionne **entièrement sur votre machine** : aucun compte, aucun serveur, aucune
donnée envoyée, aucun abonnement.

**À savoir (honnêteté)**
La correction directe dans le champ fonctionne dans la plupart des zones de texte et
éditeurs web. Elle ne fonctionne **pas dans Google Docs** (rendu en canvas) ni dans
certains éditeurs riches — pour ceux-là, utilisez la fenêtre coller/corriger/copier.

**Réglage clé**
Espace « fine » (U+202F, par défaut, ce qu'attend la QA pro) ou « compatibilité »
(U+00A0, visible sur toutes les plateformes). À vous de choisir.

---

## Permission justifications (paste one per permission in the dashboard)

- **activeTab** — Utilisé uniquement quand l'utilisateur déclenche l'extension
  (clic sur l'icône, menu contextuel, ou raccourci clavier) pour lire le texte du
  champ actif et y réécrire la version corrigée. Aucun accès à un onglet tant que
  l'utilisateur n'agit pas.
- **scripting** — Injecte, au moment où l'utilisateur déclenche une correction, le
  moteur de typographie (`engine.js`, fourni dans l'extension) et la routine de
  correction dans l'onglet courant, afin que la correction se fasse localement dans
  la page. Aucun code distant.
- **contextMenus** — Ajoute un seul élément de menu clic droit, « Corriger la
  typographie française », sur les champs modifiables et les sélections.
- **storage** — Enregistre les préférences de l'utilisateur (type d'espace : fine
  U+202F ou U+00A0, et règles activées) via `chrome.storage.sync`. Aucune donnée
  personnelle.
- **Host permissions** — **Aucune.** L'extension ne demande pas d'accès permanent
  aux sites ; elle agit seulement sur l'onglet actif, à la demande.
- **Remote code** — Aucun. **Collecte de données** — Aucune.

## Data safety / privacy (dashboard)
- Does the extension collect user data? **No.**
- Privacy policy: a one-paragraph page stating "no data is collected, transmitted, or
  stored off-device; preferences are kept locally via chrome.storage.sync." (Required
  by the store even when nothing is collected.)

## Screenshots to take (1280×800 each, 3–5 total)

1. **The popup, mid-correction** — left textarea shows `"Bonjour! Ça va?" dit-il...`,
   right shows `« Bonjour ! Ça va ? » dit-il…` — the invisible spaces made visible
   with a subtle highlight/caption arrow. (This is the money shot: the value in one glance.)
2. **Right-click menu** on a selection in a web textarea showing the
   "Corriger la typographie française" item.
3. **Before/after strip** of the four headline rules (`; ! ?` / `:` / `« »` / `%` `€` `h`),
   each line before → after, with the space characters annotated.
4. **Options page** showing the U+202F vs U+00A0 toggle with its plain-language explanation.
5. (Optional) A short caption card: "100% local · no account · no subscription · undo-safe".

## Suggested store keywords/tags
typographie, français, espace insécable, guillemets, correcteur, traducteur, ponctuation

## Price
One-time or free-with-a-small-paid-pack; ~$15 equivalent. Not a subscription (free
AutoHotkey is the alternative — compete on "works in my browser, zero setup").
