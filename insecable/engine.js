/*
 * Insécable — French typography engine
 * ------------------------------------
 * One pure, dependency-free function: fixText(text, settings).
 *
 * The SAME file runs in three places:
 *   - the extension popup (paste box), via a <script> tag;
 *   - injected into a web page (isolated world), where it sets
 *     globalThis.InsecableEngine so a follow-up injection can call it;
 *   - under Node, for the unit tests (module.exports).
 *
 * Three promises this engine keeps, in order of importance:
 *   1. IDEMPOTENT   — fixText(fixText(x)) === fixText(x). Always.
 *   2. SAFE         — it never touches URLs, emails, inline code, emoticons,
 *                     times (12:30), or primes/feet (6'2"). Those spans are
 *                     "masked" before any rule runs and restored at the end.
 *   3. fr-FR only   — anything it is not sure about, it leaves alone.
 *
 * Every non-ASCII character is built from its code point with fromCharCode so
 * the two that matter — the two invisible spaces — are unambiguous in source.
 */
(function (root) {
  'use strict';

  var CH = String.fromCharCode;
  var NNBSP      = CH(0x202F); // NARROW NO-BREAK SPACE — thin + non-breaking
  var NBSP       = CH(0x00A0); // NO-BREAK SPACE — full + non-breaking
  var GUIL_OPEN  = CH(0x00AB); // «
  var GUIL_CLOSE = CH(0x00BB); // »
  var RSQUO      = CH(0x2019); // ’  apostrophe / closing single quote
  var ELLIPSIS   = CH(0x2026); // …
  var EMDASH     = CH(0x2014); // —
  var ENDASH     = CH(0x2013); // –
  var EURO       = CH(0x20AC); // €
  var T_OPEN     = CH(0xE000); // private-use sentinels wrapping a masked
  var T_CLOSE    = CH(0xE001); // span's index

  // Any run of "space-ish" characters that might sit where a no-break space
  // belongs. We normalise all of these to the correct one — that is what makes
  // the engine idempotent and lets it repair half-corrected text.
  var ANY_SPACE = '[ \\t\\u00A0\\u202F\\u2009\\u2007\\u2008]';
  var WORD = '[\\p{L}\\p{N}]';

  var DEFAULTS = {
    mode: 'narrow', // 'narrow' -> U+202F before ; ! ? and inside guillemets
                    // 'compat' -> U+00A0 everywhere (renders on every platform)
    quotes: true,   // straight double-quote -> guillemets, straight ' -> ’
    spacing: true,  // no-break space before ; ! ? :  and inside guillemets
    symbols: true,  // 20 % , 12,50 € , 14 h 30
    dashes: true    // ...  ->  …    and    --  ->  —
  };

  // ---- masking -------------------------------------------------------------
  // Freeze spans that must never be altered. Each becomes a token no rule
  // matches; we restore them at the very end.
  function makeMasker() {
    var store = [];
    function stash(match) {
      var token = T_OPEN + store.length + T_CLOSE;
      store.push(match);
      return token;
    }
    var patterns = [
      /\bhttps?:\/\/[^\s]+/gi,        // URLs
      /\bwww\.[^\s]+/gi,              // bare www. URLs
      /\b[^\s@]+@[^\s@]+\.[^\s@]+/g,  // emails
      /`[^`]*`/g,                     // inline code spans
      /[:;]-?[)(DPpoO\/|3]+/g,        // emoticons  :)  ;-)  :D  :(
      /\d+\s*:\s*\d+/g,               // times / ratios  12:30  16:9
      /\d+['"]/g                      // primes / feet   6'   12"
    ];
    return {
      mask: function (text) {
        for (var i = 0; i < patterns.length; i++) {
          text = text.replace(patterns[i], stash);
        }
        return text;
      },
      unmask: function (text) {
        var re = new RegExp(T_OPEN + '(\\d+)' + T_CLOSE, 'g');
        var prev;
        do {
          prev = text;
          text = text.replace(re, function (_, n) { return store[+n]; });
        } while (text !== prev && re.test(text));
        return text;
      }
    };
  }

  // ---- individual passes ---------------------------------------------------

  // Straight apostrophe -> ’. French elisions (l’eau, aujourd’hui) and English
  // contractions (don’t) are unambiguous and dominate real translator text.
  function fixApostrophes(t) {
    t = t.replace(new RegExp('(' + WORD + ")'(" + WORD + ')', 'gu'), '$1' + RSQUO + '$2');
    t = t.replace(new RegExp('(' + WORD + ")'", 'gu'), '$1' + RSQUO);
    return t;
  }

  // Straight ASCII " -> guillemets, directional. We only touch the ASCII quote,
  // never existing curly quotes (which may be a deliberate English quotation).
  // Interior spacing is added later by normaliseGuillemets so the two passes
  // cannot fight and double a space.
  function fixDoubleQuotes(t) {
    var openers = '([{' + EMDASH + ENDASH + GUIL_OPEN;
    var trailingSpace = new RegExp(ANY_SPACE + '+$');
    var out = '';
    for (var i = 0; i < t.length; i++) {
      var c = t[i];
      if (c !== '"') { out += c; continue; }
      var prev = out.length ? out[out.length - 1] : '';
      var opening = prev === '' || /\s/.test(prev) || openers.indexOf(prev) >= 0;
      if (opening) {
        out += GUIL_OPEN;
      } else {
        out = out.replace(trailingSpace, '');
        out += GUIL_CLOSE;
      }
    }
    return out;
  }

  // Exactly three dots -> … (leave 4+ alone: that is an ellipsis plus a period).
  // Double hyphen -> em dash. We never promote a single hyphen — it is almost
  // always a real hyphen (compound word, range, phone number, code).
  function fixDashes(t) {
    t = t.replace(/(?<!\.)\.{3}(?!\.)/g, ELLIPSIS);
    t = t.replace(/--/g, EMDASH);
    return t;
  }

  // Exactly one interior no-break space inside « » — repairs both what we just
  // produced and guillemets the user typed with the wrong (or no) space.
  function normaliseGuillemets(t, narrow) {
    t = t.replace(new RegExp('\\u00AB' + ANY_SPACE + '*', 'g'), GUIL_OPEN + narrow);
    t = t.replace(new RegExp(ANY_SPACE + '*\\u00BB', 'g'), narrow + GUIL_CLOSE);
    return t;
  }

  // No-break space before high punctuation. The lookbehind (?<=\S) guarantees a
  // real (non-space) character precedes the mark, so we never prepend a space
  // at line start or after an opening bracket. ':' always takes the full NBSP
  // (Imprimerie nationale); ';' '!' '?' take the mode's narrow space.
  function fixHighPunct(t, narrow) {
    t = t.replace(new RegExp('(?<=\\S)' + ANY_SPACE + '*([;!?])', 'gu'), narrow + '$1');
    t = t.replace(new RegExp('(?<=\\S)' + ANY_SPACE + '*(:)', 'gu'), NBSP + '$1');
    return t;
  }

  // Symbols always take a full NO-BREAK SPACE: universally rendered and the
  // conservative default the style guides agree on.
  function fixSymbols(t) {
    t = t.replace(new RegExp('(\\d)' + ANY_SPACE + '*%', 'g'), '$1' + NBSP + '%');
    t = t.replace(new RegExp('(\\d)' + ANY_SPACE + '*\\u20AC', 'g'), '$1' + NBSP + EURO);
    t = t.replace(new RegExp('(\\d)' + ANY_SPACE + '*h' + ANY_SPACE + '*(\\d)', 'g'), '$1' + NBSP + 'h' + NBSP + '$2');
    return t;
  }

  // ---- public entry point --------------------------------------------------
  function fixText(input, settings) {
    if (typeof input !== 'string' || input.length === 0) return input;
    var s = Object.assign({}, DEFAULTS, settings || {});
    var narrow = s.mode === 'compat' ? NBSP : NNBSP;

    var masker = makeMasker();
    var t = masker.mask(input);

    if (s.quotes) { t = fixApostrophes(t); t = fixDoubleQuotes(t); }
    if (s.dashes) { t = fixDashes(t); }
    if (s.quotes || s.spacing) { t = normaliseGuillemets(t, narrow); }
    if (s.spacing) { t = fixHighPunct(t, narrow); }
    if (s.symbols) { t = fixSymbols(t); }

    return masker.unmask(t);
  }

  var api = { fixText: fixText, DEFAULTS: DEFAULTS };
  root.InsecableEngine = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
