"""
Youth Club Sports — Contact Finder + Personalized Outreach Generator
Phase 2 of club sports payment platform research.

Workflow:
  1. Load and combine both phase-1 CSVs (150 programs)
  2. Score each org as Tier 1 / 2 / 3 lead
  3. Find 2 contacts per org (staff page scrape → web search → Hunter.io)
  4. Generate personalized outreach per contact
  5. Write contacts_and_outreach.csv, tier1_priority_outreach.csv, outreach_summary_report.md
"""

import asyncio
import os
import re
import random
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent.parent
DATA_DIR    = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

CSV_ROUND1  = DATA_DIR / "club_sports_payment_platforms.csv"
CSV_ROUND2  = DATA_DIR / "club_sports_payment_platforms_100more.csv"
OUT_CONTACTS= DATA_DIR / "contacts_and_outreach.csv"
OUT_TIER1   = DATA_DIR / "tier1_priority_outreach.csv"
OUT_REPORT  = REPORTS_DIR / "outreach_summary_report.md"

CHROMIUM_EXECUTABLE = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"
USER_AGENT = "Mozilla/5.0 (compatible; research-scraper/1.0; +contact@blakewjames07@gmail.com)"
HUNTER_API_KEY = os.environ.get("HUNTER_API_KEY", "")

# ── Lead Tier Config ───────────────────────────────────────────────────────────
DIY_SIGNALS = [
    "stripe", "square", "paypal", "venmo", "wix", "squarespace",
    "google form", "cash", "check", "unknown", "custom", "none detected",
    "freshbooks", "shopify", "memberful", "sportswrench", "sportwrench",
    "elite soccer clubs", "byga", "membership.dbat", "register.munciana",
    "register.kivasports", "wordpress",
]
SMALL_PLATFORMS = ["teamsnap", "crossbar", "8to18", "jersey watch"]
ENTRENCHED = [
    "sportsengine", "stack sports", "leagueapps", "gotsoccer", "demosphere",
    "playmetrics", "blue star sports", "ryzer", "teamunify", "otto sport",
    "daysmart", "active network",
]

TPV_RANGES = {
    "Baseball":   {"min": 75_000,  "max": 600_000},
    "Lacrosse":   {"min": 60_000,  "max": 400_000},
    "Hockey":     {"min": 100_000, "max": 750_000},
    "Soccer":     {"min": 50_000,  "max": 500_000},
    "Basketball": {"min": 30_000,  "max": 200_000},
    "Volleyball": {"min": 40_000,  "max": 350_000},
    "Softball":   {"min": 50_000,  "max": 400_000},
    "Swimming":   {"min": 60_000,  "max": 450_000},
}

PLATFORM_GAPS = {
    "stack sports":  "tournament and club registration often live in different parts of the system",
    "gotsoccer":     "tournament and club registration often live in different parts of the system",
    "leagueapps":    "the travel team / multi-location experience can be inconsistent",
    "demosphere":    "the club-facing UX can feel dated compared to newer options",
    "playmetrics":   "it's well-built for elite academies but can be over-engineered for most travel programs",
    "crossbar":      "financial reporting usually ends up back in Excel",
    "teamsnap":      "it was never built for registration at scale",
    "8to18":         "it was built for school athletics — travel club features feel like add-ons",
    "teamunify":     "the parent-facing experience lags behind what families expect today",
    "ryzer":         "the pricing structure can surprise programs as they grow",
    "daysmart":      "the platform can be complex to configure for multi-team travel programs",
}

REGION_HINTS = {
    "ne": "New England", "boston": "New England", "ruffnecks": "New England",
    "nj": "New Jersey", "njrockets": "New Jersey", "avalanche": "New Jersey",
    "nyc": "New York", "ny": "New York", "rens": "New York",
    "dc": "Mid-Atlantic", "md": "Mid-Atlantic", "crab": "Maryland",
    "chicago": "Chicago", "sockers": "Chicago", "illinois": "Chicago area",
    "dallas": "Dallas", "texas": "Texas", "houston": "Texas",
    "la": "Southern California", "socal": "Southern California",
    "carolina": "Southeast", "charlotte": "Southeast",
    "michigan": "Michigan", "detroit": "Michigan",
    "colorado": "Colorado", "pikes": "Colorado",
    "midwest": "Midwest", "omaha": "Midwest",
    "atlanta": "Atlanta", "georgia": "Atlanta",
    "florida": "Florida", "orlando": "Florida",
    "phoenix": "Arizona", "coyotes": "Arizona",
    "pittsburgh": "Pittsburgh", "penguins": "Pittsburgh",
    "nashville": "Nashville",
    "connecticut": "Connecticut", "ct": "Connecticut",
    "pacific": "Pacific Northwest", "seattle": "Pacific Northwest",
    "oregon": "Pacific Northwest",
    "virginia": "Virginia", "beach": "Virginia Beach area",
}


# ── Lead Scoring ──────────────────────────────────────────────────────────────

def assign_lead_tier(platform: str, sport: str) -> dict:
    p = (platform or "").lower()
    tpv = TPV_RANGES.get(sport, {"min": 50_000, "max": 300_000})

    if not p or any(sig in p for sig in DIY_SIGNALS):
        return {
            "tier": 1,
            "rationale": "No enterprise platform — manually managing payments. Highest pain, zero switching cost.",
            **tpv,
        }
    if any(sig in p for sig in SMALL_PLATFORMS):
        return {
            "tier": 2,
            "rationale": "Using lightweight platform with known gaps. Open to upgrade if pitched correctly.",
            **tpv,
        }
    if any(sig in p for sig in ENTRENCHED):
        return {
            "tier": 3,
            "rationale": "Locked into established vendor. Pursue only at high TPV or near contract renewal.",
            **tpv,
        }
    # Unknown falls to Tier 1
    return {
        "tier": 1,
        "rationale": "Platform unclear — likely DIY or small custom build. Worth investigating.",
        **tpv,
    }


# ── Region Inference ──────────────────────────────────────────────────────────

def infer_region(row: dict) -> str:
    combined = " ".join([
        str(row.get("homepage", "")),
        str(row.get("program", "")),
        str(row.get("notes", "")),
    ]).lower()
    for key, region in REGION_HINTS.items():
        if key in combined:
            return region
    return "your region"


# ── Staff Page Scraping ───────────────────────────────────────────────────────

STAFF_SLUGS = [
    "/staff", "/about", "/about-us", "/contact", "/team",
    "/our-team", "/coaches", "/leadership", "/board", "/people",
    "/directory", "/administration",
]

TARGET_TITLES = re.compile(
    r"(executive\s+director|founder|president|owner|director|administrator|"
    r"registrar|operations|business\s+manager|club\s+director)",
    re.I,
)


def extract_contacts_from_html(html: str, source_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    contacts = []

    # Find mailto links with surrounding context
    for a_tag in soup.find_all("a", href=re.compile(r"mailto:", re.I)):
        email = a_tag["href"].replace("mailto:", "").strip().split("?")[0]
        # Walk up to find name/title
        parent = a_tag.find_parent(["div", "li", "article", "section", "td", "p"])
        name, title = None, None
        if parent:
            # Name: first strong/h-tag text
            for tag in parent.find_all(re.compile(r"h[2-6]|strong|b")):
                txt = tag.get_text(strip=True)
                if txt and 3 < len(txt) < 60:
                    name = txt
                    break
            # Title: p/span with role keywords
            for tag in parent.find_all(["p", "span", "em", "div"]):
                txt = tag.get_text(strip=True)
                if TARGET_TITLES.search(txt) and len(txt) < 80:
                    title = txt
                    break
        if email and "@" in email:
            contacts.append({
                "name":     name or "",
                "title":    title or "",
                "email":    email,
                "linkedin": "",
                "source":   "staff_page",
            })

    # Card-based staff sections
    for card in soup.find_all(
        ["div", "li", "article"],
        class_=re.compile(r"staff|team-mem|person|member|bio|coach|director|card", re.I),
    ):
        name, title, email, linkedin = None, None, None, None

        for tag in card.find_all(re.compile(r"h[2-6]|strong")):
            txt = tag.get_text(strip=True)
            if txt and 3 < len(txt) < 60:
                name = txt
                break

        for tag in card.find_all(["p", "span", "em"]):
            txt = tag.get_text(strip=True)
            if TARGET_TITLES.search(txt) and len(txt) < 80:
                title = txt
                break

        email_tag = card.find("a", href=re.compile(r"mailto:", re.I))
        if email_tag:
            email = email_tag["href"].replace("mailto:", "").strip().split("?")[0]

        li_tag = card.find("a", href=re.compile(r"linkedin\.com", re.I))
        if li_tag:
            linkedin = li_tag["href"]

        if name and TARGET_TITLES.search(title or ""):
            contacts.append({
                "name":     name,
                "title":    title or "",
                "email":    email or "",
                "linkedin": linkedin or "",
                "source":   "staff_page",
            })

    # Inline email addresses mentioned in text (backup)
    raw_emails = re.findall(
        r'\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b', html
    )
    existing_emails = {c["email"] for c in contacts}
    for em in raw_emails:
        if em not in existing_emails and not em.startswith(("no-reply", "noreply", "info@", "support@")):
            contacts.append({"name": "", "title": "", "email": em, "linkedin": "", "source": "page_text"})
            existing_emails.add(em)

    return contacts


async def scrape_staff_page(playwright, base_url: str) -> list[dict]:
    browser = await playwright.chromium.launch(
        headless=True,
        executable_path=CHROMIUM_EXECUTABLE,
        args=["--no-sandbox", "--disable-setuid-sandbox"],
    )
    context = await browser.new_context(user_agent=USER_AGENT, ignore_https_errors=True)
    page = await context.new_page()
    page.set_default_timeout(15000)

    contacts = []
    homepage = f"https://{base_url}" if not base_url.startswith("http") else base_url
    domain = urlparse(homepage).netloc

    try:
        for slug in STAFF_SLUGS:
            try:
                url = f"https://{domain}{slug}"
                resp = await page.goto(url, wait_until="domcontentloaded")
                if resp and resp.status < 400:
                    html = await page.content()
                    found = extract_contacts_from_html(html, url)
                    if found:
                        contacts.extend(found)
                        break  # Stop at first productive page
            except Exception:
                continue
    finally:
        await browser.close()

    return contacts


# ── Hunter.io Integration ─────────────────────────────────────────────────────

def hunter_domain_search(domain: str) -> list[dict]:
    if not HUNTER_API_KEY:
        return []
    try:
        resp = requests.get(
            "https://api.hunter.io/v2/domain-search",
            params={
                "domain":   domain,
                "api_key":  HUNTER_API_KEY,
                "limit":    5,
                "type":     "personal",
            },
            timeout=10,
        )
        data = resp.json()
        contacts = []
        for rec in data.get("data", {}).get("emails", []):
            contacts.append({
                "name":       f"{rec.get('first_name','')} {rec.get('last_name','')}".strip(),
                "title":      rec.get("position", ""),
                "email":      rec.get("value", ""),
                "confidence": rec.get("confidence", 0),
                "linkedin":   rec.get("linkedin", ""),
                "source":     "hunter.io",
            })
        return contacts
    except Exception:
        return []


# ── Deduplication + Ranking ───────────────────────────────────────────────────

TITLE_PRIORITY = [
    "founder", "president", "owner", "executive director",
    "director", "administrator", "registrar", "operations", "business",
    "coach", "head coach",
]


def score_title(title: str) -> int:
    t = (title or "").lower()
    for i, kw in enumerate(TITLE_PRIORITY):
        if kw in t:
            return i
    return len(TITLE_PRIORITY)


def deduplicate_and_rank(contacts: list[dict], max_results: int = 2) -> list[dict]:
    seen_names, seen_emails = set(), set()
    unique = []
    for c in contacts:
        name_key  = (c.get("name")  or "").strip().lower()
        email_key = (c.get("email") or "").strip().lower()
        if name_key in seen_names or (email_key and email_key in seen_emails):
            continue
        if name_key:
            seen_names.add(name_key)
        if email_key:
            seen_emails.add(email_key)
        unique.append(c)

    # Sort by title priority, then prefer contacts that have an email
    unique.sort(key=lambda c: (score_title(c.get("title","")), 0 if c.get("email") else 1))
    return unique[:max_results]


# ── Outreach Generation ───────────────────────────────────────────────────────

def generate_outreach(contact: dict, program: dict) -> dict:
    platform   = (program.get("platform_detected") or "unknown").lower()
    first_name = (contact.get("name") or "").split()[0] or "[Name]"
    prog_name  = program.get("program", "your program")
    sport      = program.get("sport", "sports")
    region     = infer_region(program)
    has_email  = bool(contact.get("email"))
    channel    = "email" if has_email else "linkedin"

    # ── Tier 1: DIY / Unknown ─────────────────────────────────────────────────
    if any(d in platform for d in DIY_SIGNALS) or program.get("lead_tier") == 1:
        subj = f"Quick question about {prog_name}'s registration"
        if channel == "email":
            body = (
                f"Hi {first_name},\n\n"
                f"Came across {prog_name} while researching {sport} programs in {region} — "
                f"impressive operation with a lot of moving parts each season.\n\n"
                f"Quick question: are you still handling registration and payments manually, "
                f"or through something like PayPal / Google Forms? I ask because a few programs "
                f"similar to yours have been chasing down Venmo payments and re-sending registration "
                f"links every tryout cycle — and there's a purpose-built setup worth 10 minutes of your time.\n\n"
                f"It handles online registration, payment plans, automated reminders, and parent "
                f"communication in one place — without the complexity or cost of something like SportsEngine.\n\n"
                f"Worth a quick call?\n\n"
                f"Blake James"
            )
        else:
            body = (
                f"Hi {first_name} — saw {prog_name}'s {sport} program, impressive reach across {region}.\n\n"
                f"Quick question: are you still running registration through a custom setup? "
                f"I've been talking to a few {sport} programs in a similar spot and there may be "
                f"a cleaner solution worth 10 minutes of your time.\n\n"
                f"No pitch — just want to understand how you're set up.\n\nBlake James"
            )
        return {"channel": channel, "subject": subj, "body": body}

    # ── TeamSnap ──────────────────────────────────────────────────────────────
    if "teamsnap" in platform:
        subj = f"{prog_name} — beyond what TeamSnap can do"
        body = (
            f"Hi {first_name},\n\n"
            f"Noticed {prog_name} is running on TeamSnap — solid for team communication, "
            f"but I know it starts to show cracks once you're managing multiple teams across age groups. "
            f"The payment plan management and financial reporting especially tend to fall back on spreadsheets.\n\n"
            f"A few {sport} programs in {region} have made a quiet upgrade that their admins love. "
            f"If you've thought about what comes after TeamSnap, happy to show you in 10 minutes.\n\n"
            f"Blake James"
        )
        return {"channel": channel, "subject": subj, "body": body}

    # ── Crossbar ─────────────────────────────────────────────────────────────
    if "crossbar" in platform:
        subj = f"{prog_name} — payment management beyond Crossbar"
        body = (
            f"Hi {first_name},\n\n"
            f"{prog_name} has a strong reputation in {region} {sport}. "
            f"I've seen Crossbar across a lot of AAA programs — it handles scheduling and rostering well, "
            f"but the financial side (payment plans, automated collection, consolidated reporting across teams) "
            f"usually ends up back in Excel.\n\n"
            f"If that's a pain point, I'd love to show you how a couple of other programs solved it "
            f"without ripping out what's working. 10 minutes?\n\n"
            f"Blake James"
        )
        return {"channel": channel, "subject": subj, "body": body}

    # ── 8to18 ─────────────────────────────────────────────────────────────────
    if "8to18" in platform:
        subj = f"{prog_name} — a question about your registration setup"
        body = (
            f"Hi {first_name},\n\n"
            f"Noticed {prog_name} is using 8to18 — makes sense for a school-connected program, "
            f"but I know it wasn't really built for travel/club operations at scale. "
            f"A few programs like yours have made a quiet upgrade that saved their admin staff "
            f"hours per week. Happy to walk you through it in 10 minutes — no commitment.\n\n"
            f"Blake James"
        )
        return {"channel": channel, "subject": subj, "body": body}

    # ── SportsEngine ──────────────────────────────────────────────────────────
    if "sportsengine" in platform:
        subj = f"{prog_name} — SportsEngine renewal coming up?"
        body = (
            f"Hi {first_name},\n\n"
            f"I know {prog_name} runs on SportsEngine — not here to tell you it doesn't work. "
            f"What I hear from programs your size is the cost has grown faster than the feature set, "
            f"and the renewal conversation is worth re-examining.\n\n"
            f"If you're within 6–12 months of renewal, worth a 10-minute call — "
            f"even just as leverage going into that conversation.\n\n"
            f"Blake James"
        )
        return {"channel": channel, "subject": subj, "body": body}

    # ── Entrenched platforms: Stack / LeagueApps / Demosphere / PlayMetrics ───
    gap = next(
        (v for k, v in PLATFORM_GAPS.items() if k in platform),
        "financial reporting usually ends up back in Excel",
    )
    platform_display = program.get("platform_detected", "your current platform")
    subj = f"{prog_name} — one gap I keep seeing with {platform_display}"
    body = (
        f"Hi {first_name},\n\n"
        f"{prog_name} is on a solid platform — not trying to reinvent your stack. "
        f"One thing I keep hearing from {sport} clubs using {platform_display} is that {gap}.\n\n"
        f"If that's resonating at all, there may be a point solution worth 10 minutes of your time. "
        f"If not, no worries.\n\n"
        f"Blake James"
    )
    return {"channel": channel, "subject": subj, "body": body}


# ── Report Generation ─────────────────────────────────────────────────────────

def generate_summary_report(contacts_df: pd.DataFrame, output_path: Path) -> None:
    total = len(contacts_df)
    found = contacts_df[contacts_df["contact_name"].notna() & (contacts_df["contact_name"] != "NOT FOUND")]
    not_found = contacts_df[
        contacts_df["contact_name"].isna() | (contacts_df["contact_name"] == "NOT FOUND")
    ]

    t1 = contacts_df[contacts_df["lead_tier"] == 1]
    t2 = contacts_df[contacts_df["lead_tier"] == 2]
    t3 = contacts_df[contacts_df["lead_tier"] == 3]

    platform_breakdown = (
        contacts_df.groupby("platform_detected")["program_name"]
        .nunique()
        .sort_values(ascending=False)
        .head(15)
    )

    # Top 10 Tier 1 by TPV
    top10 = (
        t1[t1["contact_name"] != "NOT FOUND"]
        .sort_values("tpv_max_est", ascending=False)
        .drop_duplicates(subset=["program_name"])
        .head(10)
    )

    lines = [
        "# Youth Club Sports — Outreach Summary Report",
        f"**Generated**: June 2026 | **Total programs**: {contacts_df['program_name'].nunique()} | **Total contact rows**: {total}",
        "",
        "---",
        "",
        "## Contact Coverage",
        "",
        f"| Metric | Count |",
        f"|---|---|",
        f"| Contacts with name found | {len(found)} |",
        f"| Contacts NOT found (manual lookup needed) | {len(not_found)} |",
        f"| Contacts with email | {contacts_df['contact_email'].notna().sum()} |",
        f"| Contacts with LinkedIn only | {(contacts_df['contact_email'].isna() & contacts_df['contact_linkedin'].notna()).sum()} |",
        "",
        "---",
        "",
        "## Lead Tier Breakdown",
        "",
        f"| Tier | Programs | Contacts | Rationale |",
        f"|---|---|---|---|",
        f"| **Tier 1 (Priority)** | {t1['program_name'].nunique()} | {len(t1)} | No platform / DIY — highest pain, zero switching cost |",
        f"| **Tier 2 (Warm)** | {t2['program_name'].nunique()} | {len(t2)} | Small/limited platform — open to upgrade |",
        f"| **Tier 3 (Cold)** | {t3['program_name'].nunique()} | {len(t3)} | Entrenched vendor — pursue only near renewal |",
        "",
        "---",
        "",
        "## Platform Distribution (Programs with Contacts Found)",
        "",
        "| Platform | Programs |",
        "|---|---|",
    ]

    for platform, count in platform_breakdown.items():
        lines.append(f"| {platform} | {count} |")

    lines += [
        "",
        "---",
        "",
        "## Orgs Requiring Manual Contact Lookup",
        "",
    ]

    manual_orgs = not_found.drop_duplicates(subset=["program_name"])[
        ["program_name", "sport", "platform_detected", "tpv_max_est", "lead_tier"]
    ]
    if not manual_orgs.empty:
        lines.append("| Program | Sport | Platform | TPV Max Est | Tier |")
        lines.append("|---|---|---|---|---|")
        for _, row in manual_orgs.sort_values("lead_tier").iterrows():
            lines.append(
                f"| {row['program_name']} | {row['sport']} | {row['platform_detected']} "
                f"| ${row['tpv_max_est']:,.0f} | {row['lead_tier']} |"
            )
    else:
        lines.append("*All orgs have at least one contact found.*")

    lines += [
        "",
        "---",
        "",
        "## 🔥 Top 10 Priority Targets (Tier 1, by TPV)",
        "",
        "*Copy-paste ready outreach for your highest-value leads.*",
        "",
    ]

    for rank, (_, row) in enumerate(top10.iterrows(), 1):
        lines += [
            f"### {rank}. {row['program_name']} ({row['sport']})",
            f"- **Contact**: {row['contact_name']} — {row['contact_title']}",
            f"- **Email**: {row['contact_email'] or 'N/A'} | **LinkedIn**: {row['contact_linkedin'] or 'N/A'}",
            f"- **Platform**: {row['platform_detected']} | **Est. TPV**: ${row['tpv_min_est']:,.0f}–${row['tpv_max_est']:,.0f}",
            f"- **Rationale**: {row['lead_rationale']}",
            "",
            f"**Channel**: {row['outreach_channel']}  ",
            f"**Subject**: {row.get('outreach_subject', '')}",
            "",
            "```",
            str(row.get("outreach_body", "")),
            "```",
            "",
        ]

    lines += [
        "---",
        "",
        "## Files",
        "",
        "| File | Description |",
        "|---|---|",
        "| `data/contacts_and_outreach.csv` | All contacts with outreach messages (one row per contact) |",
        "| `data/tier1_priority_outreach.csv` | Tier 1 leads only, sorted by TPV descending |",
        "| `reports/outreach_summary_report.md` | This file |",
    ]

    output_path.write_text("\n".join(lines))
    print(f"Report written → {output_path}")


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load and combine CSVs
    df1 = pd.read_csv(CSV_ROUND1)
    df2 = pd.read_csv(CSV_ROUND2)
    df  = pd.concat([df1, df2], ignore_index=True)
    print(f"Loaded {len(df)} programs ({len(df1)} Round 1 + {len(df2)} Round 2)")

    # Score leads
    scores = df.apply(
        lambda r: assign_lead_tier(r.get("platform_detected", ""), r.get("sport", "")),
        axis=1,
        result_type="expand",
    )
    df["lead_tier"]     = scores["tier"]
    df["lead_rationale"]= scores["rationale"]
    df["tpv_min_est"]   = scores["min"]
    df["tpv_max_est"]   = scores["max"]
    df["region"]        = df.apply(infer_region, axis=1)

    # Sort: Tier 1 first, then by TPV descending
    df = df.sort_values(["lead_tier", "tpv_max_est"], ascending=[True, False]).reset_index(drop=True)

    tier_counts = df["lead_tier"].value_counts().sort_index()
    print(f"\nLead scoring complete:")
    for tier, count in tier_counts.items():
        print(f"  Tier {tier}: {count} programs")

    all_contacts = []
    total = len(df)

    async with async_playwright() as playwright:
        for i, row in df.iterrows():
            program = row.to_dict()
            prog_name = program.get("program", "")
            homepage  = program.get("homepage", "")
            tier      = program.get("lead_tier", 3)

            print(f"\n[{i+1:03d}/{total}] [T{tier}] {prog_name} ({program.get('sport','')}) ...")

            contacts_found = []

            # Method 1: Scrape staff page (all tiers)
            if homepage and homepage != "N/A":
                try:
                    scraped = await scrape_staff_page(playwright, homepage)
                    contacts_found.extend(scraped)
                    if scraped:
                        print(f"  → Staff page: {len(scraped)} raw contacts")
                except Exception as e:
                    print(f"  → Staff page error: {e}")

            # Method 2: Hunter.io (Tier 1 and 2 only, to preserve free quota)
            if HUNTER_API_KEY and tier <= 2 and homepage:
                domain = urlparse(f"https://{homepage}").netloc or homepage
                hunter_contacts = hunter_domain_search(domain)
                contacts_found.extend(hunter_contacts)
                if hunter_contacts:
                    print(f"  → Hunter.io: {len(hunter_contacts)} contacts")

            # Deduplicate and rank
            ranked = deduplicate_and_rank(contacts_found, max_results=2)

            if not ranked:
                print(f"  ⚠  No contacts found — flagged for manual lookup")
                all_contacts.append({
                    "sport":             program.get("sport", ""),
                    "program_name":      prog_name,
                    "program_url":       homepage,
                    "lead_tier":         tier,
                    "tpv_min_est":       program.get("tpv_min_est", 0),
                    "tpv_max_est":       program.get("tpv_max_est", 0),
                    "platform_detected": program.get("platform_detected", ""),
                    "contact_name":      "NOT FOUND",
                    "contact_title":     "Manual lookup required",
                    "contact_email":     "",
                    "contact_linkedin":  "",
                    "contact_source":    "",
                    "outreach_channel":  "",
                    "outreach_subject":  "",
                    "outreach_body":     "",
                    "lead_rationale":    program.get("lead_rationale", ""),
                })
            else:
                for contact in ranked:
                    outreach = generate_outreach(contact, program)
                    print(f"  ✓  {contact.get('name','?')} ({contact.get('title','?')}) via {contact.get('source','?')}")
                    all_contacts.append({
                        "sport":             program.get("sport", ""),
                        "program_name":      prog_name,
                        "program_url":       homepage,
                        "lead_tier":         tier,
                        "tpv_min_est":       program.get("tpv_min_est", 0),
                        "tpv_max_est":       program.get("tpv_max_est", 0),
                        "platform_detected": program.get("platform_detected", ""),
                        "contact_name":      contact.get("name", ""),
                        "contact_title":     contact.get("title", ""),
                        "contact_email":     contact.get("email", ""),
                        "contact_linkedin":  contact.get("linkedin", ""),
                        "contact_source":    contact.get("source", ""),
                        "outreach_channel":  outreach["channel"],
                        "outreach_subject":  outreach.get("subject", ""),
                        "outreach_body":     outreach["body"],
                        "lead_rationale":    program.get("lead_rationale", ""),
                    })

            # Polite delay — shorter for Tier 3 (less priority)
            delay = random.uniform(1.5, 3.0) if tier <= 2 else random.uniform(0.5, 1.5)
            await asyncio.sleep(delay)

    # Write outputs
    contacts_df = pd.DataFrame(all_contacts)
    contacts_df.to_csv(OUT_CONTACTS, index=False)
    print(f"\nSaved → {OUT_CONTACTS}")

    tier1_df = contacts_df[contacts_df["lead_tier"] == 1].sort_values(
        "tpv_max_est", ascending=False
    )
    tier1_df.to_csv(OUT_TIER1, index=False)
    print(f"Saved → {OUT_TIER1}")

    generate_summary_report(contacts_df, OUT_REPORT)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"  Total programs:        {contacts_df['program_name'].nunique()}")
    print(f"  Total contact rows:    {len(contacts_df)}")
    found_mask = contacts_df["contact_name"].notna() & (contacts_df["contact_name"] != "NOT FOUND")
    print(f"  Contacts found:        {found_mask.sum()}")
    print(f"  Manual lookup needed:  {(~found_mask).sum()}")
    print(f"  Tier 1 (priority):     {(contacts_df['lead_tier']==1).sum()} contacts")
    print(f"  With email:            {contacts_df['contact_email'].notna().sum()}")


if __name__ == "__main__":
    asyncio.run(main())
