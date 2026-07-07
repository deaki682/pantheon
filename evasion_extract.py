"""Robust MD&A-narrative extractor for the evasion packets. Works for BOTH 10-Q
(MD&A = Item 2) and 10-K (Item 7), and strips the iXBRL taxonomy/context dump that
clean_html leaves at the head of modern filings (the junk that poisoned round 1)."""
import re, html

_MDNA = re.compile(r"management.{0,8}s\s+discussion\s+and\s+analysis", re.I)
_JUNK = re.compile(r"(https?://|us-gaap:|xbrli:|iso4217:|utr:|dei:|srt:|[A-Za-z]+Member\b|\bP\d+[YMD]\b)")
# a chunk qualifies as prose only if it's a real sentence-ish run of words
def _is_prose_word(w):
    return len(w)>1 and any(c.isalpha() for c in w) and not _JUNK.search(w) \
        and not re.fullmatch(r"[\d.,()%$/:+-]+", w) and not re.fullmatch(r"\d{4}-\d\d-\d\d", w)

def mdna_prose(txt, target_words=1500, min_words=400):
    txt=html.unescape(txt).replace("\xa0"," ")
    hits=list(_MDNA.finditer(txt))
    # prefer the LAST heading whose following 200 words are >=55% prose (the real section,
    # not the table-of-contents link). Fall back to whole doc.
    body=None
    for m in reversed(hits):
        seg=txt[m.end():m.end()+4000].split()[:200]
        if seg and sum(_is_prose_word(w) for w in seg)/len(seg)>=0.55:
            body=txt[m.end():]; break
    if body is None:
        body=txt
    words=body.split()
    out=[]; run_junk=0; started=False
    for w in words:
        if len(out)>=target_words: break
        if _is_prose_word(w):
            started=True; run_junk=0; out.append(w)
        else:
            run_junk+=1
            if started and run_junk>60: break   # ran into a big numeric table -> stop
    pr=" ".join(out)
    return pr if len(out)>=min_words else ""

if __name__=="__main__":
    import shared.edgar as e
    e.set_rate_limit(6)
    cik=str(next(r["cik_str"] for r in e.fetch_company_tickers_rows() if r["ticker"].upper()=="ARCC")).zfill(10)
    subs=e.fetch_submissions(cik); rec=subs["filings"]["recent"]
    j=next(i for i,f in enumerate(rec["form"]) if f=="10-Q")
    fil=e.Filing(cik=cik,accession_no=rec["accessionNumber"][j],form="10-Q",
                 filing_date=rec["filingDate"][j],primary_document=rec["primaryDocument"][j],symbol="ARCC")
    txt=e.clean_html(e.fetch_body(fil))
    pr=mdna_prose(txt)
    print(f"extracted {len(pr.split())} prose words\n")
    print(pr[:1800])
