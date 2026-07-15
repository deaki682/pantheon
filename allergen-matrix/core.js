/*
 * Menu Allergen Matrix Builder — core logic
 * -----------------------------------------
 * Pure, dependency-free. Browser (<script>) + Node (tests).
 *
 * Builds a per-item allergen matrix and disclosures from the restaurant's own menu,
 * against the 9 U.S. FDA "major food allergens" (sesame added by the FASTER Act,
 * declared like the others since Jan 1 2023). It is a mechanical disclosure aid —
 * the kind of per-item allergen grid that California's ADDE Act (SB 68, in force
 * July 1 2026) requires of restaurant chains with 20+ CA locations, and that similar
 * bills in other states have proposed. It is NOT allergen testing or a safety
 * guarantee, and the operator is responsible for the accuracy of what they mark.
 */
(function (root) {
  'use strict';

  // The 9 U.S. FDA major food allergens.
  var ALLERGENS = [
    { key: 'milk', label: 'Milk' },
    { key: 'eggs', label: 'Eggs' },
    { key: 'fish', label: 'Fish' },
    { key: 'shellfish', label: 'Crustacean shellfish' },
    { key: 'treenuts', label: 'Tree nuts' },
    { key: 'peanuts', label: 'Peanuts' },
    { key: 'wheat', label: 'Wheat' },
    { key: 'soy', label: 'Soybeans' },
    { key: 'sesame', label: 'Sesame' }
  ];

  // status: 'contains' | 'may' | '' (none/blank)
  function symbol(status) {
    if (status === 'contains') return '●'; // ●
    if (status === 'may') return '○';       // ○
    return '';
  }

  function labelFor(key) {
    for (var i = 0; i < ALLERGENS.length; i++) if (ALLERGENS[i].key === key) return ALLERGENS[i].label;
    return key;
  }

  function buildMatrix(dishes) {
    dishes = dishes || [];
    return {
      allergens: ALLERGENS.slice(),
      rows: dishes.map(function (d) {
        var a = d.allergens || {};
        return {
          name: d.name || '',
          cells: ALLERGENS.map(function (al) {
            var st = a[al.key] || '';
            return { key: al.key, status: st, symbol: symbol(st) };
          })
        };
      })
    };
  }

  // "Contains: Milk, Wheat. May contain: Tree nuts." — the per-item disclosure string.
  function dishSummary(dish) {
    var a = (dish && dish.allergens) || {};
    var contains = [], may = [];
    ALLERGENS.forEach(function (al) {
      if (a[al.key] === 'contains') contains.push(al.label);
      if (a[al.key] === 'may') may.push(al.label);
    });
    var parts = [];
    if (contains.length) parts.push('Contains: ' + contains.join(', ') + '.');
    if (may.length) parts.push('May contain: ' + may.join(', ') + '.');
    if (!parts.length) return 'No major allergens declared.';
    return parts.join(' ');
  }

  // Flags dishes that need attention before printing.
  function validate(dishes) {
    dishes = dishes || [];
    var w = [];
    if (!dishes.length) { w.push('Add at least one menu item.'); return w; }
    dishes.forEach(function (d, i) {
      if (!d.name || !d.name.trim()) w.push('Item ' + (i + 1) + ' has no name.');
      var a = d.allergens || {};
      var any = ALLERGENS.some(function (al) { return a[al.key]; });
      if (!any && !d.confirmedNone) {
        w.push('"' + (d.name || 'Item ' + (i + 1)) + '" has no allergens marked — confirm it truly contains none.');
      }
    });
    return w;
  }

  var LEGEND = '● = contains  ·  ○ = may contain (made in a kitchen that also handles this allergen)';
  var STANDARD_NOTE =
    'Allergen information is provided by this establishment based on standard recipes and ' +
    'supplier information. Because items are prepared in a shared kitchen, we cannot ' +
    'guarantee against cross-contact. Please tell your server about any allergies.';

  var api = {
    ALLERGENS: ALLERGENS, symbol: symbol, labelFor: labelFor,
    buildMatrix: buildMatrix, dishSummary: dishSummary, validate: validate,
    LEGEND: LEGEND, STANDARD_NOTE: STANDARD_NOTE
  };
  root.AllergenCore = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
