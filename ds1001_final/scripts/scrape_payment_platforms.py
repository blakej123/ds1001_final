"""
Youth Travel/Club Sports Payment Platform Scraper

Visits 50 major youth club sports websites to identify their payment/registration
software platform by scanning page source, redirect URLs, iframes, and footer text.
"""

import asyncio
import random
import re
import time
from urllib.parse import urljoin, urlparse

import pandas as pd
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

CHROMIUM_EXECUTABLE = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"

USER_AGENT = (
    "Mozilla/5.0 (compatible; research-scraper/1.0; +contact@blakewjames07@gmail.com)"
)

PLATFORM_PATTERNS = {
    "SportsEngine": [r"sportsengine\.com", r"se-i\.com", r"se-cdn\.com", r"nbcsports.*engine"],
    "TeamSnap": [r"teamsnap\.com", r"go\.teamsnap\.com"],
    "Stack Sports": [
        r"stacksports\.com",
        r"gotsoccer\.com",
        r"affinity\.com",
        r"stackreg\.com",
        r"stack\.com/sports",
    ],
    "LeagueApps": [r"leagueapps\.(com|io)", r"powered\s+by\s+leagueapps"],
    "Ryzer": [r"ryzerapp\.com", r"ryzercheckout\.com"],
    "8to18": [r"8to18(media)?\.com"],
    "Crossbar": [r"crossbar\.org", r"\.crossbar\.org"],
    "Demosphere": [r"demosphere\.(com|net)"],
    "Playmetrics": [r"playmetrics\.com"],
    "Blue Star Sports": [r"bluestarsports\.(com|net)"],
    "Jersey Watch": [r"jerseywatch\.com"],
    "USSSA": [r"usssa\.com"],
    "Perfect Game": [r"perfectgame\.org/register", r"perfectgame\.org/account"],
    "Stripe": [r"js\.stripe\.com", r"stripe\.com/v[23]", r"stripe\.com/js"],
    "Square": [r"squareup\.com", r"square\.com/payment", r"squarespace-cdn.*square"],
    "PayPal": [r"paypal\.com/cgi-bin", r"paypalobjects\.com", r"paypal\.me/"],
    "Wix": [r"wix\.com", r"wixstatic\.com", r"wixsite\.com"],
    "Squarespace": [r"squarespace\.com", r"sqsp\.net", r"squarespace-cdn\.com"],
    "Acuity Scheduling": [r"acuityscheduling\.com"],
    "GiveSmart": [r"givesmart\.com"],
    "iClassPro": [r"iclassproregistration\.com", r"iclassapp\.com"],
    "Sportninja": [r"sportninja\.com"],
    "Ramp": [r"rampcooling\.com", r"rampinteractive\.com"],
    "SportsSignUp": [r"sportssignup\.com"],
    "TeamUnify": [r"teamunify\.com"],
    "Active Network": [r"active\.com", r"activenetwork\.com"],
}

REG_LINK_KEYWORDS = [
    "register",
    "registration",
    "tryout",
    "tryouts",
    "join",
    "enroll",
    "sign-up",
    "signup",
    "payment",
    "pay-now",
    "paynow",
    "membership",
]


def detect_platforms(text: str) -> str:
    found = []
    for platform, patterns in PLATFORM_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                found.append(platform)
                break
    return ", ".join(found) if found else "Unknown / Custom"


async def find_reg_link(page, base_url: str) -> str | None:
    for kw in REG_LINK_KEYWORDS:
        links = await page.query_selector_all(f"a[href*='{kw}' i]")
        if links:
            href = await links[0].get_attribute("href")
            if href:
                if href.startswith("http"):
                    return href
                return urljoin(base_url, href)
    return None


async def gather_page_evidence(page) -> str:
    """Collect page source + iframe srcs + current URL into one string for scanning."""
    source = await page.content()
    current_url = page.url

    iframe_srcs = []
    try:
        iframes = await page.query_selector_all("iframe")
        for iframe in iframes:
            src = await iframe.get_attribute("src")
            if src:
                iframe_srcs.append(src)
    except Exception:
        pass

    return source + " " + current_url + " " + " ".join(iframe_srcs)


async def scrape_program(playwright, program: dict) -> dict:
    browser = await playwright.chromium.launch(
        headless=True,
        executable_path=CHROMIUM_EXECUTABLE,
        args=["--no-sandbox", "--disable-setuid-sandbox"],
    )
    context = await browser.new_context(
        user_agent=USER_AGENT,
        ignore_https_errors=True,
    )
    page = await context.new_page()
    page.set_default_timeout(20000)

    result = {
        "sport": program["sport"],
        "program": program["name"],
        "homepage": program["url"],
        "registration_url": "",
        "platform_detected": "",
        "notes": "",
    }

    try:
        homepage = f"https://{program['url']}"
        await page.goto(homepage, wait_until="domcontentloaded")

        # Check homepage evidence first
        hp_evidence = await gather_page_evidence(page)

        # Try to find and follow a registration link
        reg_url = await find_reg_link(page, page.url)

        if reg_url:
            try:
                await page.goto(reg_url, wait_until="domcontentloaded")
                result["registration_url"] = page.url
            except Exception:
                result["registration_url"] = reg_url

        reg_evidence = await gather_page_evidence(page)
        combined = hp_evidence + " " + reg_evidence

        result["platform_detected"] = detect_platforms(combined)

        # Pull footer text for notes
        try:
            soup = BeautifulSoup(reg_evidence, "lxml")
            footer = soup.find("footer")
            if footer:
                footer_text = footer.get_text(separator=" ", strip=True)[:300]
                result["notes"] = footer_text
        except Exception:
            pass

    except Exception as e:
        result["notes"] = f"Error: {str(e)[:200]}"
    finally:
        await browser.close()

    return result


PROGRAMS = [
    # ── BASEBALL ──────────────────────────────────────────────────────────
    {"sport": "Baseball", "name": "Canes Baseball", "url": "canesbaseball.net"},
    {"sport": "Baseball", "name": "East Cobb Baseball", "url": "eastcobbbaseball.com"},
    {"sport": "Baseball", "name": "Texas Baseball Ranch", "url": "texasbaseballranch.com"},
    {"sport": "Baseball", "name": "Perfect Game (PGBA)", "url": "perfectgame.org"},
    {"sport": "Baseball", "name": "Area Codes Baseball", "url": "areacodebaseball.com"},
    {"sport": "Baseball", "name": "ExtraInnings Baseball", "url": "extrainningsbaseball.com"},
    {"sport": "Baseball", "name": "Elite Baseball of Lemont", "url": "elitebaseballoflemont.com"},
    {"sport": "Baseball", "name": "Baseball Youth", "url": "baseballyouth.com"},
    {"sport": "Baseball", "name": "Diamond Sports", "url": "diamondsportsinc.com"},
    {"sport": "Baseball", "name": "EvoShield Canes (Southeast)", "url": "canesbaseball.net/southeast"},
    # ── LACROSSE ──────────────────────────────────────────────────────────
    {"sport": "Lacrosse", "name": "3d Lacrosse", "url": "3dlacrosse.com"},
    {"sport": "Lacrosse", "name": "True Lacrosse", "url": "truelacrosse.com"},
    {"sport": "Lacrosse", "name": "Predators Lacrosse", "url": "predatorslacrosse.com"},
    {"sport": "Lacrosse", "name": "Leading Edge Lacrosse", "url": "leadingedgelacrosse.com"},
    {"sport": "Lacrosse", "name": "Laxachusetts", "url": "laxachusetts.com"},
    {"sport": "Lacrosse", "name": "MadLax", "url": "madlax.com"},
    {"sport": "Lacrosse", "name": "Chesapeake Bayhawks Youth", "url": "bayhawksyouth.com"},
    {"sport": "Lacrosse", "name": "Trilogy Lacrosse", "url": "trilogylacrosse.com"},
    {"sport": "Lacrosse", "name": "Express Lacrosse", "url": "expresslacrosse.com"},
    {"sport": "Lacrosse", "name": "Annapolis Hawks", "url": "annapolishawks.com"},
    # ── HOCKEY ────────────────────────────────────────────────────────────
    {"sport": "Hockey", "name": "Little Caesars AAA Hockey", "url": "littlecaesarshockey.com"},
    {"sport": "Hockey", "name": "Shattuck-St. Mary's Hockey", "url": "shattucksaintmarys.org"},
    {"sport": "Hockey", "name": "Chicago Mission AAA", "url": "chicagomission.com"},
    {"sport": "Hockey", "name": "Honeybaked Hockey", "url": "honeybakedhockey.com"},
    {"sport": "Hockey", "name": "Tri-City Storm", "url": "stormhockey.com"},
    {"sport": "Hockey", "name": "Boston Jr. Bruins", "url": "jrbruins.com"},
    {"sport": "Hockey", "name": "Team Illinois Hockey", "url": "teamillib.com"},
    {"sport": "Hockey", "name": "Colorado Thunderbirds", "url": "coloradothunderbirds.org"},
    {"sport": "Hockey", "name": "New Jersey Rockets", "url": "njrockets.com"},
    {"sport": "Hockey", "name": "St. Louis Blues Elite Hockey", "url": "stlblueselite.com"},
    # ── SOCCER ────────────────────────────────────────────────────────────
    {"sport": "Soccer", "name": "Solar SC", "url": "solarsc.com"},
    {"sport": "Soccer", "name": "Surf Soccer Club", "url": "surfsoccer.com"},
    {"sport": "Soccer", "name": "FC Dallas Youth", "url": "fcdallas.com"},
    {"sport": "Soccer", "name": "NCFC Youth", "url": "ncfcyouth.com"},
    {"sport": "Soccer", "name": "Eclipse Select SC", "url": "eclipseselect.org"},
    {"sport": "Soccer", "name": "PDA Soccer", "url": "pdasoccer.com"},
    {"sport": "Soccer", "name": "LA Galaxy Academy", "url": "lagalaxy.com"},
    {"sport": "Soccer", "name": "Concorde Fire", "url": "concordefire.com"},
    {"sport": "Soccer", "name": "Houston Dash Academy", "url": "houstondash.com"},
    {"sport": "Soccer", "name": "Sporting KC Academy", "url": "sportingkc.com"},
    # ── BASKETBALL ────────────────────────────────────────────────────────
    {"sport": "Basketball", "name": "Team Takeover", "url": "teamtakeoverhoops.com"},
    {"sport": "Basketball", "name": "Brad Beal Elite", "url": "bradbeaelite.com"},
    {"sport": "Basketball", "name": "Oakland Soldiers", "url": "oaklandsoldiersbasketball.com"},
    {"sport": "Basketball", "name": "Mokan Elite", "url": "mokanelite.com"},
    {"sport": "Basketball", "name": "PSA Cardinals", "url": "psacardinals.com"},
    {"sport": "Basketball", "name": "All In Elite", "url": "allineliteua.com"},
    {"sport": "Basketball", "name": "Team Penny", "url": "teampennyaau.com"},
    {"sport": "Basketball", "name": "NY Rens", "url": "nyrens.org"},
    {"sport": "Basketball", "name": "Nightrydas Elite", "url": "nightrydaselite.com"},
    {"sport": "Basketball", "name": "Howard Pulley Panthers", "url": "howardpulleypanthers.com"},
]


async def main():
    results = []
    total = len(PROGRAMS)

    async with async_playwright() as playwright:
        for i, program in enumerate(PROGRAMS, 1):
            print(f"[{i:02d}/{total}] Scraping: {program['name']} ({program['sport']}) ...")
            result = await scrape_program(playwright, program)
            results.append(result)
            print(f"         Platform: {result['platform_detected'] or 'Not detected'}")
            if result["notes"] and result["notes"].startswith("Error"):
                print(f"         {result['notes'][:80]}")
            # Polite crawl delay with jitter
            await asyncio.sleep(random.uniform(1.5, 3.5))

    df = pd.DataFrame(results, columns=["sport", "program", "homepage", "registration_url", "platform_detected", "notes"])
    out_path = "club_sports_payment_platforms.csv"
    df.to_csv(out_path, index=False)
    print(f"\nSaved → {out_path}")

    print("\n" + "=" * 60)
    print("PLATFORM FREQUENCY (all 50 programs)")
    print("=" * 60)
    # Each program may list multiple platforms; expand and count individually
    all_platforms = []
    for v in df["platform_detected"]:
        if v and v != "Unknown / Custom":
            all_platforms.extend([p.strip() for p in v.split(",")])
        else:
            all_platforms.append("Unknown / Custom")
    platform_series = pd.Series(all_platforms).value_counts()
    print(platform_series.to_string())

    print("\n" + "=" * 60)
    print("RESULTS BY SPORT")
    print("=" * 60)
    for sport in df["sport"].unique():
        sport_df = df[df["sport"] == sport]
        print(f"\n── {sport.upper()} ──")
        print(sport_df[["program", "platform_detected"]].to_string(index=False))

    unknown = df[df["platform_detected"].isin(["Unknown / Custom", ""])]
    if not unknown.empty:
        print("\n" + "=" * 60)
        print("PROGRAMS WITH UNDETERMINED PLATFORM")
        print("=" * 60)
        print(unknown[["sport", "program", "registration_url"]].to_string(index=False))

    return df


if __name__ == "__main__":
    asyncio.run(main())
