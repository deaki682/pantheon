/*
 * Funeral Rule Price List Generator — core logic
 * ----------------------------------------------
 * Pure, dependency-free. Runs in the browser (via <script>) and under Node (tests).
 *
 * It assembles the four documents the FTC "Funeral Rule" (16 CFR Part 453) requires
 * a funeral provider to give consumers, from the home's own items and prices:
 *   - GPL   General Price List
 *   - CPL   Casket Price List
 *   - OBCPL Outer Burial Container Price List
 *   - SFGS  Statement of Funeral Goods and Services Selected
 *
 * The mandatory-disclosure sentences below are the FTC model-rule language. The Rule
 * was amended recently and states add their own requirements, so the app frames every
 * output as a DRAFT to review — it does not claim to guarantee compliance.
 */
(function (root) {
  'use strict';

  // ---- FTC model mandatory disclosures (16 CFR 453.2 / 453.3) ----
  var DISCLOSURES = {
    // GPL: itemization / non-declinable basic services fee
    itemization:
      'You may choose only the items you desire. However, any funeral arrangements ' +
      'you select will include a charge for our basic services and overhead. If legal ' +
      'or other requirements mean you must buy any items you did not specifically ask ' +
      'for, we will explain the reason in writing on the statement we provide ' +
      'describing the funeral goods and services you selected.',
    basicServicesFee:
      'This fee for our basic services and overhead will be added to the total cost of ' +
      'the funeral arrangements you select. (This fee is already included in our charges ' +
      'for direct cremations, immediate burials, and forwarding or receiving remains.)',
    embalming:
      'Except in certain special cases, embalming is not required by law. Embalming may ' +
      'be necessary, however, if you select certain funeral arrangements, such as a ' +
      'funeral with viewing. You do not have to pay for embalming you did not approve if ' +
      'you selected arrangements such as a direct cremation or immediate burial. If we ' +
      'charged for embalming, we will explain why in writing on the statement we provide ' +
      'describing the funeral goods and services you selected.',
    alternativeContainer:
      'If you want to arrange a direct cremation, you can use an alternative container. ' +
      'Alternative containers encase the body and can be made of materials like ' +
      'fiberboard or composition materials (with or without an outside covering). The ' +
      'containers we provide are: ',
    casketList:
      'A complete price list of the caskets we offer is available for your review.',
    outerContainerList:
      'In most areas of the country, state or local law does not require that you buy a ' +
      'container to surround the casket in the grave. However, many cemeteries require ' +
      'that you have such a container so that the grave will not sink in. Either a grave ' +
      'liner or a burial vault will satisfy these requirements. A complete price list of ' +
      'the outer burial containers we offer is available for your review.'
  };

  // ---- The 16 GPL categories the Rule expects (order is flexible) ----
  // required:true items must appear (with a price or a note) for a complete GPL.
  var GPL_CATEGORIES = [
    { key: 'basic_services', label: 'Basic services of funeral director and staff', required: true, disclosure: 'basicServicesFee' },
    { key: 'embalming', label: 'Embalming', required: true, disclosure: 'embalming' },
    { key: 'other_prep', label: 'Other preparation of the body', required: true },
    { key: 'facilities_viewing', label: 'Use of facilities and staff for viewing', required: true },
    { key: 'facilities_ceremony', label: 'Use of facilities and staff for funeral ceremony', required: true },
    { key: 'facilities_memorial', label: 'Use of facilities and staff for memorial service', required: true },
    { key: 'facilities_graveside', label: 'Use of facilities and staff for graveside service', required: true },
    { key: 'hearse', label: 'Transfer of remains to funeral home / hearse', required: true },
    { key: 'limousine', label: 'Limousine', required: false },
    { key: 'forwarding', label: 'Forwarding of remains to another funeral home', required: true },
    { key: 'receiving', label: 'Receiving remains from another funeral home', required: true },
    { key: 'direct_cremation', label: 'Direct cremation', required: true, disclosure: 'alternativeContainer' },
    { key: 'immediate_burial', label: 'Immediate burial', required: true },
    { key: 'caskets', label: 'Caskets', required: true, disclosure: 'casketList' },
    { key: 'outer_containers', label: 'Outer burial containers', required: false, disclosure: 'outerContainerList' }
  ];

  function money(n) {
    var v = Number(n);
    if (!isFinite(v)) return '';
    return '$' + v.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  }

  // Assemble the GPL as structured sections (app.js renders to printable HTML).
  function buildGPL(home, items, opts) {
    home = home || {};
    items = items || {};
    opts = opts || {};
    var lines = GPL_CATEGORIES.map(function (cat) {
      var entry = items[cat.key] || {};
      return {
        key: cat.key,
        label: cat.label,
        price: entry.price != null && entry.price !== '' ? money(entry.price) : '',
        note: entry.note || '',
        required: cat.required,
        disclosure: cat.disclosure ? DISCLOSURES[cat.disclosure] : ''
      };
    });
    // The alternative-container disclosure names the actual containers offered.
    var altText = DISCLOSURES.alternativeContainer + (opts.alternativeContainers || '[list your alternative containers]') + '.';
    return {
      title: 'General Price List',
      home: home,
      effectiveDate: opts.effectiveDate || '',
      itemizationNotice: DISCLOSURES.itemization,
      lines: lines,
      alternativeContainerDisclosure: altText
    };
  }

  function buildPriceList(title, home, rows) {
    return {
      title: title,
      home: home || {},
      rows: (rows || []).map(function (r) {
        return { name: r.name || '', description: r.description || '', price: r.price != null && r.price !== '' ? money(r.price) : '' };
      })
    };
  }

  // Statement of Funeral Goods and Services Selected — the itemized end document.
  function buildStatement(home, selected, opts) {
    selected = selected || [];
    opts = opts || {};
    var subtotal = selected.reduce(function (s, it) {
      var v = Number(it.price);
      return s + (isFinite(v) ? v : 0);
    }, 0);
    return {
      title: 'Statement of Funeral Goods and Services Selected',
      home: home || {},
      decedent: opts.decedent || '',
      date: opts.date || '',
      items: selected.map(function (it) {
        return { label: it.label || '', price: it.price != null && it.price !== '' ? money(it.price) : '', declined: !!it.declined };
      }),
      total: money(subtotal),
      totalRaw: subtotal,
      legalRequirementsNote:
        'The goods and services shown are those you selected. Charges are only for those ' +
        'items that are used. If we are required by law or by a cemetery or crematory to ' +
        'use any items, we will explain the reason in writing below.'
    };
  }

  // Validation: flag missing required categories/disclosures BEFORE the home prints.
  function validateGPL(items) {
    items = items || {};
    var warnings = [];
    GPL_CATEGORIES.forEach(function (cat) {
      if (!cat.required) return;
      var entry = items[cat.key];
      var hasPrice = entry && entry.price != null && entry.price !== '';
      var hasNote = entry && entry.note;
      if (!hasPrice && !hasNote) {
        warnings.push('Missing required item: "' + cat.label + '" (enter a price, or a note such as "priced individually").');
      }
    });
    return warnings;
  }

  var api = {
    DISCLOSURES: DISCLOSURES,
    GPL_CATEGORIES: GPL_CATEGORIES,
    money: money,
    buildGPL: buildGPL,
    buildPriceList: buildPriceList,
    buildStatement: buildStatement,
    validateGPL: validateGPL
  };
  root.FuneralCore = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
