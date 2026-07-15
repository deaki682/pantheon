# Offline Superbill — validation kit

**The point of this folder: find out if people will pay BEFORE we build.** No product yet — just a
landing page and this outreach plan. We build only if the numbers below clear the bar.

The bet in one line: cash-pay / out-of-network clinicians already pay $15–99/mo for cloud superbill
tools that hold their clients' PHI. Nobody sells the **offline, no-account, pay-once** version. We're
testing whether the privacy + one-time-price wedge is worth real money — starting with the emptiest,
sharpest corner: **lactation consultants (IBCLCs)**.

---

## Step 1 — Put the page live (15 min)

1. **Wire the form.** Create a free form endpoint and paste its URL into `index.html` where it says
   `action="https://formspree.io/f/REPLACE_ME"`.
   - **Formspree** (formspree.io) — free tier, 50 submissions/mo, emails you each entry. Easiest.
   - Or **Tally** / **Basin** / a Google Form (swap the whole form block for the embed).
2. **Host it.** It's one static file — drag the folder onto **Netlify Drop** (app.netlify.com/drop),
   or Cloudflare Pages / GitHub Pages. You get a public URL in a minute. Free.
3. (Optional, stronger signal — see Step 3) add a real **$29 pre-order** button.

## Step 2 — The go / kill bar (decide this now, honor it later)

Drive ~200–400 relevant clinicians to the page (the posts below reach that). Then:

- **BUILD IT if:** ≥ 25–40 email signups **and** ≥ 10 pick *"Yes — I'd buy it"* on the $29 question,
  **and** at least a handful say the privacy angle is why (watch the replies, not just the form).
- **STRONG BUILD if:** you add a pre-order button and ≥ 3–5 people actually pay $29 up front.
- **KILL IT if:** signups are near-zero despite real reach, **or** the dominant answer is
  *"No — I'd only use a free tool" / "Office Ally is free."* That's the whole risk of this niche, and
  it's cheaper to learn it here than after building. If it dies, we move to the runner-up (tip-pool or
  process-server) with the same test.

Give it ~1–2 weeks. Don't move the goalposts.

## Step 3 — Stronger signal (optional but recommended): a real pre-order

Money talks louder than emails. On **Payhip** or **Gumroad**, create a $29 product titled
"Offline Superbill (pre-order)" with the description: *"Ships within 2 weeks. Full refund anytime, no
questions."* Swap the "Get early access" button `href` to that checkout. Anyone who pays is a
validated buyer; refund every one of them at launch or if they ask. Even 3–5 pre-orders is a far
stronger green light than 40 emails.

---

## Step 4 — Seed it (value-first, not spammy)

Rule: **lead with a question, not a pitch.** These communities ban ad-drops; you'll do far better
asking for feedback on a problem than announcing a product. Post as yourself, be honest that you're a
solo dev exploring this.

### Reddit — r/lactation, r/IBCLC, r/therapists, r/dietitians, r/privatepractice
> **Title:** OON clinicians — how do you make superbills without putting client data in a cloud tool?
>
> I'm a solo developer. Talking to out-of-network folks, I keep hearing the same thing: the superbill
> tools are monthly subscriptions that store your clients' PHI, and the "private" workaround is a
> password-protected Word doc you rebuild every month. So I'm prototyping a superbill maker that runs
> 100% in your browser — nothing uploaded, no account, one-time price — and I'd love a gut check from
> people who actually do this. Does that solve a real annoyance for you, or is your current setup fine?
> (Mocked up the idea here if it's useful to react to: [LINK] — genuinely after feedback, not sales.)

*Check each sub's self-promo rules first; some want you to use a "feedback"/"I made this" flair or to
have comment history. If a sub is strict, just ask the question and skip the link — DM it to people
who bite.*

### Facebook groups (this is where IBCLCs actually are)
Search for and join: **"Private Practice IBCLC," "Lactation Private Practice," "Lactation Consultants
in Private Practice," "Dietitians in Private Practice," "Private Practice Therapists."**
> Quick question for the private-practice folks 👋 How are you making superbills for your OON clients
> right now — a paid platform, an EHR, or a Word/Excel template? I'm building a little tool that makes
> the superbill PDF entirely on your own computer (nothing uploaded, no monthly fee) because a few of
> you told me you don't love your client data sitting in a cloud service. Would that be useful, or is
> what you've got working fine? Mock-up here if you want to react: [LINK]

### Also worth a look
- **IBCLC / lactation Discords and forums**, ProZ-style profession boards.
- The people who commented "Office Ally is clunky" on review sites — DM them.

---

## Step 5 — Talk to 8–15 of them (the real signal)

Signups are weak evidence; a 10-minute call is strong. Offer $10 or nothing — many will chat for free
if you're clearly not selling. Ask, and mostly listen:

1. Walk me through how you make a superbill today, start to finish.
2. What tool or template is that? What do you pay for it?
3. What's the most annoying part? (let them answer before you suggest anything)
4. How do you feel about your clients' info living in that tool / the cloud? Ever think about it?
5. Have you ever had a client's superbill get rejected or reimbursed slowly? What happened?
6. If a tool made the superbill on your own computer — nothing uploaded, no account — would that
   matter to you, or is that not a concern?
7. What would you expect to pay for something like that? Monthly, or one-time?
8. Would you pay $29 once for it, honestly? (watch the hesitation, not just the word)
9. What would make it a no-brainer vs. a no?
10. Who else should I talk to?

**What you're listening for:** do they bring up privacy/PHI *unprompted* (real wedge) or only when you
mention it (weak wedge)? Do they wince at their current tool, or shrug? Three unprompted "ugh yes, I
hate that my client data is in [tool]" + a willing $29 is the green light.

---

## If it validates
Come back and I'll build the real thing in a weekend — the offline superbill generator (client-side
PDF, localStorage, the same tested + offline-license stack we've already shipped), starting with the
exact fields IBCLCs need, plus the No Surprises Act Good Faith Estimate bundled as the compliance
sweetener. Then the landing page becomes the real store page.

## If it doesn't
We killed it for the price of a domain and a week of DMs — exactly the point of testing first. Next in
line: **tip-pool/tronc** (higher ceiling, real backend) or **process-server affidavit** (tight money
linkage, smaller slice). Same landing-page test, different niche.
