#!/usr/bin/env python3
"""
Compile contacts and generate personalized outreach for 150 youth sports programs.
Outputs: contacts_and_outreach.csv, tier1_priority_outreach.csv, outreach_summary_report.md
"""

import csv
import os
from pathlib import Path
from datetime import date

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

# ── TPV ranges by sport ($K/year) ──────────────────────────────────────────────
TPV = {
    "Hockey":     (100, 750),
    "Baseball":   (75,  600),
    "Soccer":     (50,  500),
    "Lacrosse":   (60,  400),
    "Volleyball": (40,  350),
    "Softball":   (50,  400),
    "Swimming":   (60,  450),
    "Basketball": (30,  200),
}

# ── Lead tier scoring ──────────────────────────────────────────────────────────
ENTRENCHED = [
    "sportsengine","sportngin","leagueapps","gotsoccer","demosphere",
    "playmetrics","teamunify","gomotion","stack sports","ryzer","daysmart",
    "active network","otto sport","blue star sports","futureteam",
]
SMALL_PLATFORMS = ["crossbar","teamsnap","8to18","jersey watch"]


def score_tier(platform: str) -> int:
    p = str(platform or "").lower()
    if any(s in p for s in ENTRENCHED):
        return 3
    if any(s in p for s in SMALL_PLATFORMS):
        return 2
    return 1


def tier_rationale(platform: str, tier: int) -> str:
    p = str(platform or "").lower()
    if tier == 1:
        return "DIY/Custom/Unknown — highest switching potential"
    if tier == 2:
        return f"Small platform ({platform}) — upgrade opportunity"
    for e in ENTRENCHED:
        if e in p:
            nice = {
                "sportsengine": "SportsEngine", "sportngin": "SportsEngine",
                "leagueapps": "LeagueApps", "teamunify": "TeamUnify",
                "gomotion": "TeamUnify (GoMotion)", "playmetrics": "PlayMetrics",
                "demosphere": "Demosphere / OTTO Sport AI",
                "stack sports": "Stack Sports", "ryzer": "Ryzer",
                "daysmart": "DaySmart Recreation",
            }.get(e, platform)
            return f"Entrenched ({nice}) — low switching, but high volume"
    return f"Entrenched ({platform})"


# ── Verified contacts (name, title, email, linkedin, source) ──────────────────
# Format: program_name → list of up to 2 contact dicts
CONTACTS_DB = {
    # ── HOCKEY ────────────────────────────────────────────────────────────────
    "Chicago Mission AAA": [
        {"name": "Tom Mandarino",  "title": "Girls Program Director",
         "email": "tomd@jrmission.com",    "linkedin": "",
         "source": "chicagomission.com staff page"},
        {"name": "Gino Cavallini", "title": "Boys Program Director",
         "email": "ginoc@jrmission.com",   "linkedin": "",
         "source": "chicagomission.com staff page"},
    ],
    "Buffalo Jr. Sabres": [
        {"name": "Pat Kaleta",    "title": "President / Hockey Director",
         "email": "info@buffalojrsabres.com", "linkedin": "",
         "source": "buffalojrsabres.com"},
        {"name": "Sean Wallace",  "title": "Executive Director (20U)",
         "email": "sean.wallace@harborcenter.com", "linkedin": "",
         "source": "Harbor Center / Buffalo Jr. Sabres"},
    ],
    "Little Caesars AAA Hockey": [
        {"name": "Brian Rolston", "title": "Director of Hockey",
         "email": "info@lcfhhockey.org", "linkedin": "",
         "source": "littlecaesarshockey.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit littlecaesarshockey.com/staff"},
    ],
    "Boston Jr. Bruins": [
        {"name": "Mike Anderson", "title": "Staff / Program Director",
         "email": "mike@bostonjuniorbruins.com", "linkedin": "",
         "source": "bostonjuniorbruins.org"},
        {"name": "Research Required", "title": "Executive Director",
         "email": "", "linkedin": "",
         "source": "Visit bostonjuniorbruins.org/staff"},
    ],
    "New Jersey Rockets": [
        {"name": "Dave Ball",     "title": "Hockey Director",
         "email": "info@rocketshockeyclub.com", "linkedin": "",
         "source": "rocketshockeyclub.com/about/rhc-staff"},
        {"name": "David Gibson",  "title": "Owner / Founder",
         "email": "", "linkedin": "",
         "source": "rocketshockeyclub.com"},
    ],
    "Connecticut Polar Bears": [
        {"name": "Kathy Pippy",   "title": "Director of Girls Hockey",
         "email": "info@ctpb.com", "linkedin": "",
         "source": "ctpb.com"},
        {"name": "Research Required", "title": "Boys Hockey Director",
         "email": "", "linkedin": "",
         "source": "Visit ctpb.com/staff"},
    ],
    "Omaha AAA Hockey": [
        {"name": "David Wilkie",  "title": "President",
         "email": "info@omahaaaahockeyclub.com", "linkedin": "",
         "source": "omahaahockey.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit omahaahockey.com/contact"},
    ],
    "St. Louis Blues Elite Hockey": [
        {"name": "Matt Heffington", "title": "Executive Director",
         "email": "aaabluesdirector@gmail.com", "linkedin": "",
         "source": "stlaaablues.com announcement"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit stlaaablues.com/contact"},
    ],
    "Shattuck-St. Mary's Hockey": [
        {"name": "Research Required", "title": "Director of Hockey",
         "email": "admissions@s-sm.org", "linkedin": "",
         "source": "s-sm.org/athletics/hockey — boarding school model"},
        {"name": "Research Required", "title": "Summer Hockey Camp Director",
         "email": "", "linkedin": "",
         "source": "Visit s-sm.org/hockey-center"},
    ],
    "Team Illinois Hockey": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "", "linkedin": "",
         "source": "teamillinois.com — verify correct domain"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Manual research required"},
    ],
    "North Jersey Avalanche": [
        {"name": "Research Required", "title": "Hockey Director / Owner",
         "email": "", "linkedin": "",
         "source": "northjerseyavalanche.com — research staff page"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Manual research required"},
    ],
    "Western Mass Warriors": [
        {"name": "Research Required", "title": "Hockey Director",
         "email": "", "linkedin": "",
         "source": "westernmasswarriors.com — verify org exists"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Manual research required"},
    ],
    "Honeybaked Hockey": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@honeybakedhockey.com", "linkedin": "",
         "source": "honeybakedhockey.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit honeybakedhockey.com/staff"},
    ],
    "Tri-City Storm": [
        {"name": "Research Required", "title": "Hockey Director",
         "email": "info@stormhockey.com", "linkedin": "",
         "source": "stormhockey.com"},
        {"name": "Research Required", "title": "General Manager",
         "email": "", "linkedin": "",
         "source": "Visit stormhockey.com/contact"},
    ],
    "Colorado Thunderbirds": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@coloradothunderbirds.org", "linkedin": "",
         "source": "coloradothunderbirds.org"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit tbirdhockey.org/staff"},
    ],
    "Pittsburgh Penguins Elite": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@pittsburghpenguinselite.com", "linkedin": "",
         "source": "pittsburghpenguinselite.com"},
        {"name": "Research Required", "title": "Hockey Director",
         "email": "", "linkedin": "",
         "source": "Visit pittsburghpenguinselite.sportngin.com"},
    ],
    "Detroit Compuware": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@compuwarehockey.com", "linkedin": "",
         "source": "compuwarehockey.com"},
        {"name": "Research Required", "title": "Hockey Director",
         "email": "", "linkedin": "",
         "source": "Visit compuwarehockey.sportngin.com"},
    ],
    "Dallas Stars Elite": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@dallasstarselite.com", "linkedin": "",
         "source": "dallasstarselite.com"},
        {"name": "Research Required", "title": "Hockey Director",
         "email": "", "linkedin": "",
         "source": "Visit dsehc.sportngin.com"},
    ],
    "Carolina Jr. Hurricanes": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@juniorhurricanes.com", "linkedin": "",
         "source": "juniorhurricanes.com"},
        {"name": "Research Required", "title": "Hockey Director",
         "email": "", "linkedin": "",
         "source": "Visit juniorhurricanes.leagueapps.com"},
    ],
    "Green Bay Jr. Gamblers": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@gbjrgamblers.com", "linkedin": "",
         "source": "gbjrgamblers.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit gbjrgamblers.com.app.crossbar.org"},
    ],
    "Nashville Jr. Predators": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@jrpredators.com", "linkedin": "",
         "source": "jrpredators.com"},
        {"name": "Research Required", "title": "Hockey Director",
         "email": "", "linkedin": "",
         "source": "Visit jrpredators.leagueapps.com"},
    ],
    "Phoenix Jr. Coyotes": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@jrcoyotes.org", "linkedin": "",
         "source": "jrcoyotes.org"},
        {"name": "Research Required", "title": "Hockey Director",
         "email": "", "linkedin": "",
         "source": "Visit jrcoyotes.sportngin.com"},
    ],
    "Minnesota Wild Youth": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@mnwildhockey.com", "linkedin": "",
         "source": "mnwildhockey.com"},
        {"name": "Research Required", "title": "Hockey Director",
         "email": "", "linkedin": "",
         "source": "Visit wildicehockey.sportngin.com"},
    ],
    "Los Angeles Jr. Kings": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@lajrkings.com", "linkedin": "",
         "source": "lajrkings.com"},
        {"name": "Research Required", "title": "Hockey Director",
         "email": "", "linkedin": "",
         "source": "Visit lajrkings.sportngin.com"},
    ],
    "San Jose Jr. Sharks": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@jrsharkshockey.com", "linkedin": "",
         "source": "jrsharkshockey.com"},
        {"name": "Research Required", "title": "Hockey Director",
         "email": "", "linkedin": "",
         "source": "Visit jrsharkshockey.sportngin.com"},
    ],

    # ── BASEBALL ──────────────────────────────────────────────────────────────
    "Canes Baseball": [
        {"name": "Jeff Petty",   "title": "Founder / President & CEO",
         "email": "info@canesbaseball.net", "linkedin": "",
         "source": "canesbaseball.net/canes-baseball-20-years-of-excellence/"},
        {"name": "Dan Gitzen",   "title": "General Manager",
         "email": "info@canesbaseball.net", "linkedin": "",
         "source": "canesbaseball.net/staff/"},
    ],
    "EvoShield Canes (Southeast)": [
        {"name": "Jeff Petty",   "title": "Founder / President & CEO",
         "email": "info@canesbaseball.net", "linkedin": "",
         "source": "canesbaseball.net — SE chapter of Canes network"},
        {"name": "Research Required", "title": "Southeast Regional Director",
         "email": "", "linkedin": "",
         "source": "Visit canesbaseball.net/southeast"},
    ],
    "Canes Midwest": [
        {"name": "Research Required", "title": "Midwest Regional Director",
         "email": "info@canesmidwestbaseball.com", "linkedin": "",
         "source": "canesmidwestbaseball.com"},
        {"name": "Sammy Serrano", "title": "Central Regional Director",
         "email": "", "linkedin": "",
         "source": "canesbaseball.net/canes-tab-sammy-serrano-as-central-regional-director/"},
    ],
    "East Cobb Baseball": [
        {"name": "Guerry Baldwin", "title": "Executive Director",
         "email": "guerry@eastcobbbaseball.com", "linkedin": "",
         "source": "eastcobbbaseball.com/about/staff/ (20+ year director)"},
        {"name": "Kevin Baldwin",  "title": "Vice President",
         "email": "kbaldwin@eastcobbbaseball.com", "linkedin": "",
         "source": "ZoomInfo / eastcobbbaseball.com"},
    ],
    "Texas Baseball Ranch": [
        {"name": "Ron Wolforth",  "title": "Founder / CEO",
         "email": "", "linkedin": "linkedin.com/in/ron-wolforth-01951684",
         "source": "texasbaseballranch.com / LinkedIn"},
        {"name": "Research Required", "title": "Operations Director",
         "email": "info@texasbaseballranch.com", "linkedin": "",
         "source": "Visit texasbaseballranch.com/staff"},
    ],
    "Perfect Game (PGBA)": [
        {"name": "Rob Ponger",   "title": "CEO",
         "email": "", "linkedin": "",
         "source": "Perfect Game press release / PitchBook"},
        {"name": "Jerry Ford",   "title": "Founder",
         "email": "", "linkedin": "",
         "source": "Fox Business / perfectgame.org"},
    ],
    "Area Codes Baseball": [
        {"name": "Ronny Torres",  "title": "Vice President",
         "email": "info@areacodebaseball.com", "linkedin": "",
         "source": "areacodebaseball.com / web search"},
        {"name": "Research Required", "title": "Director / President",
         "email": "info@areacodebaseball.com", "linkedin": "",
         "source": "areacodebaseball.com/contact"},
    ],
    "ExtraInnings Baseball": [
        {"name": "Research Required", "title": "Founder / Director",
         "email": "", "linkedin": "",
         "source": "Site may be defunct — research extrainningsbaseball.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Manual research required"},
    ],
    "Elite Baseball of Lemont": [
        {"name": "Research Required", "title": "Founder / Director",
         "email": "", "linkedin": "",
         "source": "elitebaseballoflemont.com — verify domain"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Manual research required"},
    ],
    "Baseball Youth": [
        {"name": "Jim Haddaway",  "title": "CEO / Founder (Athletx Sports Group)",
         "email": "info@baseballyouth.com", "linkedin": "",
         "source": "baseballyouth.com / Athletx Sports Group"},
        {"name": "Research Required", "title": "Director of Operations",
         "email": "", "linkedin": "",
         "source": "Visit baseballyouth.com/contact"},
    ],
    "Diamond Sports": [
        {"name": "Research Required", "title": "Founder / Director",
         "email": "", "linkedin": "",
         "source": "diamondsportsinc.com — verify domain"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Manual research required"},
    ],
    "Baseball Factory": [
        {"name": "Research Required", "title": "CEO / President",
         "email": "info@baseballfactory.com", "linkedin": "",
         "source": "baseballfactory.com"},
        {"name": "Research Required", "title": "Director of Operations",
         "email": "", "linkedin": "",
         "source": "Visit baseballfactory.com/staff"},
    ],
    "Future Stars Series": [
        {"name": "Research Required", "title": "President / Director",
         "email": "info@futurestarsseries.com", "linkedin": "",
         "source": "futurestarsseries.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit futurestarsseries.com/contact"},
    ],
    "USSSA Baseball": [
        {"name": "John J. Latella", "title": "CEO",
         "email": "info@usssa.com", "linkedin": "",
         "source": "usssa.com/contact / web search"},
        {"name": "Research Required", "title": "Director of Baseball",
         "email": "", "linkedin": "",
         "source": "Visit usssa.com/contact"},
    ],
    "Select Baseball": [
        {"name": "Research Required", "title": "President / Director",
         "email": "info@selectbaseballclub.com", "linkedin": "",
         "source": "selectbaseballclub.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit selectbaseball.leagueapps.com"},
    ],
    "New England Ruffnecks": [
        {"name": "Research Required", "title": "President / Director",
         "email": "info@neruffnecks.com", "linkedin": "",
         "source": "neruffnecks.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit neruffnecks.leagueapps.com"},
    ],
    "Texas Bombers Baseball": [
        {"name": "Research Required", "title": "President / Director",
         "email": "info@texasbombers.com", "linkedin": "",
         "source": "texasbombers.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit texasbombers.square.site"},
    ],
    "D-BAT Academies": [
        {"name": "Research Required", "title": "CEO / President",
         "email": "info@dbat.com", "linkedin": "",
         "source": "dbat.com"},
        {"name": "Research Required", "title": "Director of Operations",
         "email": "", "linkedin": "",
         "source": "Visit membership.dbat.net"},
    ],
    "Team One Baseball": [
        {"name": "Research Required", "title": "President / Director",
         "email": "info@teamonebaseball.com", "linkedin": "",
         "source": "teamonebaseball.com (Baseball Factory family)"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit teamonebaseball.com/contact"},
    ],
    "Ripken Baseball": [
        {"name": "Research Required", "title": "CEO / President",
         "email": "info@ripkenbaseball.com", "linkedin": "",
         "source": "ripkenbaseball.com"},
        {"name": "Research Required", "title": "Director of Operations",
         "email": "", "linkedin": "",
         "source": "Visit ripkenbaseball.leagueapps.com"},
    ],
    "Five Tool Baseball": [
        {"name": "Research Required", "title": "President / Director",
         "email": "info@fivetoolbaseball.com", "linkedin": "",
         "source": "fivetoolbaseball.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit fivetool.leagueapps.com"},
    ],
    "Prep Baseball Report (PBR)": [
        {"name": "Research Required", "title": "CEO / Founder",
         "email": "info@prepbaseballreport.com", "linkedin": "",
         "source": "prepbaseballreport.com"},
        {"name": "Research Required", "title": "Director of Events",
         "email": "", "linkedin": "",
         "source": "Visit prepbaseballreport.com/contact"},
    ],
    "USA Baseball Youth Events": [
        {"name": "Research Required", "title": "Executive Director / CEO",
         "email": "info@usabaseball.com", "linkedin": "",
         "source": "usabaseball.com — national governing body"},
        {"name": "Research Required", "title": "Director of Youth Programs",
         "email": "", "linkedin": "",
         "source": "Visit usabaseball.com/contact"},
    ],
    "Mid-South Baseball": [
        {"name": "Research Required", "title": "Founder / Director",
         "email": "", "linkedin": "",
         "source": "midsouthbaseball.com — research required"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Manual research required"},
    ],
    "Power Baseball": [
        {"name": "Research Required", "title": "Founder / Director",
         "email": "", "linkedin": "",
         "source": "powerbaseballnational.com — research required"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Manual research required"},
    ],

    # ── SOCCER ────────────────────────────────────────────────────────────────
    "Solar SC": [
        {"name": "Ellen Llamas",       "title": "President",
         "email": "ellamas@solarsoccerclub.com", "linkedin": "",
         "source": "solarsoccerclub.net/our-club/front-office/ + PR Newswire"},
        {"name": "Stephanie Landreneau", "title": "Club Administrator",
         "email": "admin@solarsoccerclub.net", "linkedin": "",
         "source": "solarsoccerclub.net/our-club/front-office/"},
    ],
    "Surf Soccer Club": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@surfsoccer.com", "linkedin": "",
         "source": "surfsoccer.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit members.surfsoccer.com"},
    ],
    "FC Dallas Youth": [
        {"name": "Chris Hayden",    "title": "VP / Boys Academy Director",
         "email": "chayden@fcdallas.com", "linkedin": "",
         "source": "fcdallas.com/youth/fcdyfrontoffice"},
        {"name": "Attalie Morgan",  "title": "Registrar",
         "email": "amorgan@fcdallas.com", "linkedin": "",
         "source": "fcdallas.com/youth/fcdyfrontoffice"},
    ],
    "NCFC Youth": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@ncfcyouth.com", "linkedin": "",
         "source": "ncfcyouth.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit ncfcyouth.com/contact"},
    ],
    "Eclipse Select SC": [
        {"name": "Enrique Peguero Jr", "title": "CEO / Founder",
         "email": "info@eclipseselect.org",
         "linkedin": "linkedin.com/in/enrique-peguero-jr-1884475a",
         "source": "LinkedIn / eclipseselect.org"},
        {"name": "Sarah Dames",        "title": "CFO",
         "email": "sarah@eclipseselect.org", "linkedin": "",
         "source": "eclipseselect.org staff"},
    ],
    "PDA Soccer": [
        {"name": "Tom Anderson",    "title": "President",
         "email": "info@pdasoccer.org", "linkedin": "",
         "source": "pdasoccer.org/PDA-staff.aspx"},
        {"name": "Gerry McKeown",   "title": "Boys Executive Director",
         "email": "", "linkedin": "",
         "source": "pdasoccer.org/PDA-staff.aspx"},
    ],
    "LA Galaxy Academy": [
        {"name": "Research Required", "title": "Youth Academy Director",
         "email": "info@youth.lagalaxy.com", "linkedin": "",
         "source": "youth.lagalaxy.com"},
        {"name": "Research Required", "title": "Director of Youth Programs",
         "email": "", "linkedin": "",
         "source": "Visit lagalaxy.com/youth"},
    ],
    "Concorde Fire": [
        {"name": "Eric Steinhauser", "title": "Executive Director",
         "email": "ericsteinhauser@concordefire.com", "linkedin": "",
         "source": "concordefire.com/concorde-info/club-info/directors-and-staff/"},
        {"name": "Larry Lord",       "title": "President",
         "email": "info@concordefire.com", "linkedin": "",
         "source": "concordefire.com"},
    ],
    "Houston Dash Academy": [
        {"name": "Research Required", "title": "Academy Director",
         "email": "info@houstondynamoyouth.com", "linkedin": "",
         "source": "houstondash.com / houstondynamoyouth.leagueapps.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit houstondynamoyouth.leagueapps.com"},
    ],
    "Sporting KC Academy": [
        {"name": "Research Required", "title": "Academy Director",
         "email": "info@sportingkc.com", "linkedin": "",
         "source": "sportingkc.com / sportingkcacademy.com"},
        {"name": "Research Required", "title": "Director of Youth Programs",
         "email": "", "linkedin": "",
         "source": "Visit sportingkcacademy.com/contact"},
    ],
    "RSL Arizona": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@rsl-az.com", "linkedin": "",
         "source": "rsl-az.com"},
        {"name": "Research Required", "title": "Academy Director",
         "email": "", "linkedin": "",
         "source": "Visit rsl-az.sportngin.com"},
    ],
    "Michigan Hawks": [
        {"name": "Doug Landefeld",   "title": "Executive Director",
         "email": "doug@hawks.soccer", "linkedin": "",
         "source": "michiganhawks.com"},
        {"name": "Michele Krzisnik", "title": "Director of Coaching",
         "email": "mrkrzisnik@gmail.com", "linkedin": "",
         "source": "michiganhawks.com staff page"},
    ],
    "Sockers FC Chicago": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@sockersfc.com", "linkedin": "",
         "source": "sockersfc.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit sportsengine.com/org/sockers-fc-chicago"},
    ],
    "Ohio Premier Soccer": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@ohiopremier.com", "linkedin": "",
         "source": "ohiopremier.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit ohiopremier.sportngin.com"},
    ],
    "GPS Massachusetts": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@gpsmassachusetts.com", "linkedin": "",
         "source": "gpsmassachusetts.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit gpsmassachusetts.sportngin.com"},
    ],
    "Weston FC": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@westonfc.org", "linkedin": "",
         "source": "westonfc.org"},
        {"name": "Research Required", "title": "Registrar",
         "email": "", "linkedin": "",
         "source": "Visit westonfc.org/contact"},
    ],
    "Beach FC": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@beachfc.com", "linkedin": "",
         "source": "beachfc.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit beachfc.sportngin.com"},
    ],
    "Crossfire Premier": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@crossfirepremier.com", "linkedin": "",
         "source": "crossfirepremier.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit crossfirepremier.sportngin.com"},
    ],
    "Florida Premier FC": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@floridapremierfc.com", "linkedin": "",
         "source": "floridapremierfc.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit floridapremierfc.sportngin.com"},
    ],
    "FC Stars Massachusetts": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@fcstars.org", "linkedin": "",
         "source": "fcstars.org"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit fcstars.org/contact"},
    ],
    "St. Louis Scott Gallagher": [
        {"name": "Brad Davis",       "title": "President",
         "email": "info@slsgsoccer.com", "linkedin": "",
         "source": "slsgsoccer.com/staff"},
        {"name": "Research Required", "title": "Executive Director",
         "email": "", "linkedin": "",
         "source": "Visit slsgsoccer.com/staff"},
    ],
    "Heat FC (San Diego)": [
        {"name": "Research Required", "title": "Executive Director / President",
         "email": "info@heatfc.com", "linkedin": "",
         "source": "heatfc.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit fcheat.elitesoccerclubs.com"},
    ],
    "Albion SC": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@albionsc.com", "linkedin": "",
         "source": "albionsc.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit sportsengine.com/org/albion-sc"},
    ],
    "Charlotte Soccer Academy": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@charlottesocceracademy.com", "linkedin": "",
         "source": "charlottesocceracademy.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit charlottesocceracademy.leagueapps.com"},
    ],
    "Tampa Bay United": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@tampabayunited.com", "linkedin": "",
         "source": "tampabayunited.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit sportsengine.com/org/tampa-bay-united"},
    ],

    # ── BASKETBALL ────────────────────────────────────────────────────────────
    "Team Takeover": [
        {"name": "Keith Stevens",   "title": "Founder / Director",
         "email": "info@team-takeover.com", "linkedin": "",
         "source": "team-takeover.com"},
        {"name": "Research Required", "title": "Program Director",
         "email": "", "linkedin": "",
         "source": "Visit team-takeover.com/contact"},
    ],
    "Brad Beal Elite": [
        {"name": "Tim Holloway",    "title": "President / Executive Director",
         "email": "", "linkedin": "",
         "source": "bradleybealelite.com / web search (314-479-5897)"},
        {"name": "Megan Jackson",   "title": "Staff",
         "email": "", "linkedin": "linkedin.com/in/megan-jackson-575408271",
         "source": "LinkedIn"},
    ],
    "Oakland Soldiers": [
        {"name": "Greg Davis",      "title": "Executive Director",
         "email": "info@soldierbasketball.com", "linkedin": "",
         "source": "soldierbasketball.com"},
        {"name": "Lance Olivier",   "title": "Director of Player Personnel",
         "email": "lance@soldierbasketball.com", "linkedin": "",
         "source": "ZoomInfo / soldierbasketball.com"},
    ],
    "Mokan Elite": [
        {"name": "Matt Suther",     "title": "Founder / Director",
         "email": "info@mokanbasketball.com", "linkedin": "",
         "source": "mokanbasketball.com"},
        {"name": "Research Required", "title": "Program Director",
         "email": "", "linkedin": "",
         "source": "Visit mokanbasketball.com/contact"},
    ],
    "PSA Cardinals": [
        {"name": "Terrance 'Munch' Williams", "title": "Director / Founder",
         "email": "info@psacardinals.com", "linkedin": "",
         "source": "psacardinals.com"},
        {"name": "Research Required", "title": "Program Director",
         "email": "", "linkedin": "",
         "source": "Visit psacardinals.com/contact"},
    ],
    "All In Elite": [
        {"name": "Ryan Silver",     "title": "Founder / Director",
         "email": "info@allineliteua.com", "linkedin": "",
         "source": "allineliteua.com/contact-us"},
        {"name": "Research Required", "title": "Program Director",
         "email": "", "linkedin": "",
         "source": "Visit allineliteua.com/contact-us"},
    ],
    "Team Penny": [
        {"name": "Research Required", "title": "Director / Founder",
         "email": "", "linkedin": "",
         "source": "teampennyaau.com — verify domain; pennyhardawaybasketballcamp.com"},
        {"name": "Research Required", "title": "Program Director",
         "email": "", "linkedin": "",
         "source": "Manual research required"},
    ],
    "NY Rens": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@nyrhoops.org", "linkedin": "",
         "source": "nyrhoops.org"},
        {"name": "Research Required", "title": "Program Director",
         "email": "", "linkedin": "",
         "source": "Visit nyrhoops.sportngin.com"},
    ],
    "Nightrydas Elite": [
        {"name": "Jordan Maurice",  "title": "Director / Founder",
         "email": "nightrydaselite@gmail.com", "linkedin": "",
         "source": "nightrydaselite.com / web search"},
        {"name": "Research Required", "title": "Program Director",
         "email": "", "linkedin": "",
         "source": "Visit nightrydaselite.com/contact"},
    ],
    "Howard Pulley Panthers": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@howardpulleybasketball.com", "linkedin": "",
         "source": "howardpulleybasketball.com"},
        {"name": "Research Required", "title": "Program Director",
         "email": "", "linkedin": "",
         "source": "Visit howardpulleybasketball.sportngin.com"},
    ],
    "Expressions Elite": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@expressionselite.com", "linkedin": "",
         "source": "expressionselite.com"},
        {"name": "Research Required", "title": "Program Director",
         "email": "", "linkedin": "",
         "source": "Visit sportsengine.com/org/expressions-elite"},
    ],
    "Drive Nation": [
        {"name": "Research Required", "title": "Founder / Director",
         "email": "info@drivenation.com", "linkedin": "",
         "source": "drivenation.com"},
        {"name": "Research Required", "title": "Program Director",
         "email": "", "linkedin": "",
         "source": "Visit drivenation.com/contact"},
    ],
    "Mass Rivals": [
        {"name": "Vin Pastore",     "title": "Program Director",
         "email": "questions@rivalsbasketball.com", "linkedin": "",
         "source": "ZoomInfo / rivalsbasketball.com (3 Step Sports LLC)"},
        {"name": "Research Required", "title": "Executive Director",
         "email": "", "linkedin": "",
         "source": "Visit massrivals.sportngin.com"},
    ],
    "King James Shooting Stars": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@shootingstarsbball.com", "linkedin": "",
         "source": "shootingstarsbball.com (LeBron James Akron program)"},
        {"name": "Research Required", "title": "Program Director",
         "email": "", "linkedin": "",
         "source": "Visit shootingstarsbb.leagueapps.com"},
    ],
    "Georgia Stars": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@gastars.org", "linkedin": "",
         "source": "gastars.org"},
        {"name": "Research Required", "title": "Program Director",
         "email": "", "linkedin": "",
         "source": "Visit gastars.org/contact"},
    ],
    "Texas Titans": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@titanshoop.com", "linkedin": "",
         "source": "titanshoop.com"},
        {"name": "Research Required", "title": "Program Director",
         "email": "", "linkedin": "",
         "source": "Visit sportsengine.com/org/texas-titans-basketball"},
    ],
    "Colorado Hawks": [
        {"name": "Research Required", "title": "Founder / Director",
         "email": "", "linkedin": "",
         "source": "coloradohawksbasketball.com — research required"},
        {"name": "Research Required", "title": "Program Director",
         "email": "", "linkedin": "",
         "source": "Manual research required"},
    ],
    "New England Playmakers": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@neplaymakers.com", "linkedin": "",
         "source": "neplaymakers.com"},
        {"name": "Research Required", "title": "Program Director",
         "email": "", "linkedin": "",
         "source": "Visit neplaymakers.leagueapps.com"},
    ],
    "Team Texas": [
        {"name": "Research Required", "title": "Founder / Director",
         "email": "", "linkedin": "",
         "source": "teamtexashoops.com — research required"},
        {"name": "Research Required", "title": "Program Director",
         "email": "", "linkedin": "",
         "source": "Manual research required"},
    ],
    "Philly Pride": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@phillypridebball.com", "linkedin": "",
         "source": "phillypridebball.com"},
        {"name": "Research Required", "title": "Program Director",
         "email": "", "linkedin": "",
         "source": "Visit pridebasketball21usa.leagueapps.com"},
    ],
    "Houston Defenders": [
        {"name": "Research Required", "title": "Founder / Director",
         "email": "", "linkedin": "",
         "source": "houstondefenders.com — research required"},
        {"name": "Research Required", "title": "Program Director",
         "email": "", "linkedin": "",
         "source": "Manual research required"},
    ],
    "Dream Vision NY": [
        {"name": "Research Required", "title": "Founder / Director",
         "email": "", "linkedin": "",
         "source": "dreamvisionny.com — research required"},
        {"name": "Research Required", "title": "Program Director",
         "email": "", "linkedin": "",
         "source": "Manual research required"},
    ],
    "Indiana Elite": [
        {"name": "Research Required", "title": "Founder / Director",
         "email": "info@indianaelitebasketball.com", "linkedin": "",
         "source": "indianaelitebasketball.com"},
        {"name": "Research Required", "title": "Program Director",
         "email": "", "linkedin": "",
         "source": "Visit indianaelitebasketball.com/contact"},
    ],
    "Oregon Nike Elite": [
        {"name": "Research Required", "title": "Founder / Director",
         "email": "", "linkedin": "",
         "source": "oregonnike.org — research required"},
        {"name": "Research Required", "title": "Program Director",
         "email": "", "linkedin": "",
         "source": "Manual research required"},
    ],
    "Seattle Rotary": [
        {"name": "Research Required", "title": "Executive Director / Founder",
         "email": "info@rotarystylebasketball.org", "linkedin": "",
         "source": "rotarystylebasketball.org (est. 1991)"},
        {"name": "Research Required", "title": "Program Director",
         "email": "", "linkedin": "",
         "source": "Visit rotarystylebasketball.org/contact"},
    ],

    # ── LACROSSE ──────────────────────────────────────────────────────────────
    "3d Lacrosse": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@3dlacrosse.com", "linkedin": "",
         "source": "3dlacrosse.com (3STEP Sports family)"},
        {"name": "Research Required", "title": "National Director",
         "email": "", "linkedin": "",
         "source": "Visit register.threestep.com"},
    ],
    "True Lacrosse": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@truelacrosse.com", "linkedin": "",
         "source": "truelacrosse.com"},
        {"name": "Research Required", "title": "National Director",
         "email": "", "linkedin": "",
         "source": "Visit truelacrosse.leagueapps.com"},
    ],
    "Predators Lacrosse": [
        {"name": "Eric Greenberg",    "title": "CEO / Founder",
         "email": "info@predatorslacrosse.com",
         "linkedin": "linkedin.com/in/eric-greenberg-a6b833165",
         "source": "LinkedIn / predatorslacrosse.com"},
        {"name": "Alexandra Goldstein", "title": "Girls Program Director",
         "email": "", "linkedin": "",
         "source": "predatorslacrosse.com staff page"},
    ],
    "Leading Edge Lacrosse": [
        {"name": "Marc Moreau",       "title": "Director",
         "email": "info@leadingedgeelite.com", "linkedin": "",
         "source": "LeagueApps case study (leadingedgeelite.com)"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit leadingedgeelite.leagueapps.com"},
    ],
    "Laxachusetts": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@laxachusetts.com", "linkedin": "",
         "source": "laxachusetts.com (Marshfield MA)"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit sportsengine.com/org/laxachusetts"},
    ],
    "MadLax": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@madlax.com", "linkedin": "",
         "source": "madlax.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit sportsengine.com/org/madlax-3478"},
    ],
    "Chesapeake Bayhawks Youth": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "", "linkedin": "",
         "source": "bayhawksyouth.com — site not resolving; research required"},
        {"name": "Research Required", "title": "Program Director",
         "email": "", "linkedin": "",
         "source": "Manual research required"},
    ],
    "Trilogy Lacrosse": [
        {"name": "Research Required", "title": "Founder / Director",
         "email": "info@trilogylacrosse.com", "linkedin": "",
         "source": "trilogylacrosse.com (founded by Ryan Boyle & Rob Lindsey)"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit trilogylacrosse.leagueapps.com"},
    ],
    "Express Lacrosse": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@expresslacrosse.com", "linkedin": "",
         "source": "expresslacrosse.com (Long Island Express flagship)"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit liexpress.leagueapps.com"},
    ],
    "Annapolis Hawks": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "hawkslacrosse@outlook.com", "linkedin": "",
         "source": "annapolishawks.com / annapolishawks.leagueapps.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit annapolishawks.leagueapps.com"},
    ],
    "Crabs Lacrosse": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@crabslax.com", "linkedin": "",
         "source": "crabslax.com (Maryland premier program)"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit crabslax.leagueapps.com"},
    ],
    "Sweetlax Florida": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@sweetlaxflorida.com", "linkedin": "",
         "source": "sweetlaxflorida.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit slflorida.leagueapps.com"},
    ],
    "Atlas Lacrosse Club": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@atlaslacroseclub.com", "linkedin": "",
         "source": "atlaslacroseclub.com (PLL Juniors NY Atlas)"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit nyatlasyouth-pll.leagueapps.com"},
    ],
    "Lax Factory": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@laxfactory.com", "linkedin": "",
         "source": "laxfactory.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit laxfactory.leagueapps.com"},
    ],
    "DC Express Lacrosse": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@dcexpresslacrosse.com", "linkedin": "",
         "source": "dcexpresslacrosse.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit dcexpress.leagueapps.com"},
    ],
    "Pride Lacrosse New England": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@pridelacrosse.com", "linkedin": "",
         "source": "pridelacrosse.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit pridelacrosse.leagueapps.com"},
    ],
    "Ultimate Lacrosse": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@ultimategoallacrosse.com", "linkedin": "",
         "source": "ultimategoallacrosse.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit ultimategoallacrosse.leagueapps.com"},
    ],
    "CT Hammerheads": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@cthammerheads.com", "linkedin": "",
         "source": "cthammerheads.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit hammerheadlacrosse.sportngin.com"},
    ],
    "Big 4 Lacrosse": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@big4lacrosse.com", "linkedin": "",
         "source": "big4lacrosse.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit big4lacrosseboys.leagueapps.com"},
    ],
    "Carolina LAX": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@carolinalax.com", "linkedin": "",
         "source": "carolinalax.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit teamcarolinalax.leagueapps.com"},
    ],

    # ── VOLLEYBALL ────────────────────────────────────────────────────────────
    "A5 Volleyball": [
        {"name": "Gabe Aramian",    "title": "Executive Director",
         "email": "info@a5volleyball.com", "linkedin": "",
         "source": "a5volleyball.com (30+ national championship titles)"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "tom@a5volleyball.com", "linkedin": "",
         "source": "a5volleyball.com/contact"},
    ],
    "Munciana Volleyball": [
        {"name": "Mike Lingenfelter", "title": "Co-Director",
         "email": "info@munciana.com",
         "linkedin": "linkedin.com/in/mike-lingenfelter-5a4a1348",
         "source": "munciana.com / LinkedIn"},
        {"name": "Research Required",  "title": "Co-Director / Administrator",
         "email": "", "linkedin": "",
         "source": "Visit munciana.com/contact (note: 3STEP Sports affiliation)"},
    ],
    "Colorado Fusion VBC": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@coloradofusionvbc.com", "linkedin": "",
         "source": "coloradofusionvbc.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit fusionvbc.leagueapps.com"},
    ],
    "Long Beach Volleyball Club": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@lbvc.net", "linkedin": "",
         "source": "lbvc.net"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit longbeachvbc.sportngin.com"},
    ],
    "Elevate Volleyball": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@elevatevolleyball.com", "linkedin": "",
         "source": "elevatevolleyball.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit elevatevolleyball.sportngin.com"},
    ],
    "KIVA Volleyball": [
        {"name": "Courtney Robison-Dixon", "title": "Director / Staff",
         "email": "courtney@kivasports.net", "linkedin": "",
         "source": "kivasports.net"},
        {"name": "Research Required",       "title": "Club Administrator",
         "email": "maryann@kivasports.net", "linkedin": "",
         "source": "kivasports.net/contact"},
    ],
    "Beverly Bandits VB": [
        {"name": "Research Required", "title": "Director",
         "email": "", "linkedin": "",
         "source": "NOTE: Beverly Bandits is primarily a softball org; no confirmed VB club"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Manual research required"},
    ],
    "Club Gold Volleyball (TX)": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@clubgoldvb.com", "linkedin": "",
         "source": "clubgoldvb.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit clubgoldvb.sportngin.com"},
    ],
    "Sports Performance VBC": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@spvbc.net", "linkedin": "",
         "source": "spvbc.net (Sacramento Performance VBC)"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit sacperformancevb.sportngin.com"},
    ],
    "Crossroads of America VBC": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@coavolleyball.com", "linkedin": "",
         "source": "coavolleyball.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit coavolleyball.sportngin.com"},
    ],
    "Club K Volleyball": [
        {"name": "Research Required", "title": "Founder / Director",
         "email": "", "linkedin": "",
         "source": "clubkvolleyball.com — research required"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Manual research required"},
    ],
    "Great Plains Region Volleyball": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@greatplainsvolleyball.org", "linkedin": "",
         "source": "greatplainsvolleyball.org (Omaha NE regional governing body)"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit greatplainsregionalvolleyball.sportngin.com"},
    ],
    "Illinois Valley Juniors VBC": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@ivjvbc.com", "linkedin": "",
         "source": "ivjvbc.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit illinoisjuniors.sportngin.com"},
    ],
    "NOVA Volleyball": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@novavbc.com", "linkedin": "",
         "source": "novavbc.com (Northern Virginia)"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit novaprestigevolleyball.sportngin.com"},
    ],
    "Rox Volleyball": [
        {"name": "Research Required", "title": "Founder / Director",
         "email": "", "linkedin": "",
         "source": "roxvb.com (Shopify-based custom platform)"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit roxvb.com/contact"},
    ],

    # ── SOFTBALL ──────────────────────────────────────────────────────────────
    "Texas Bombers Gold": [
        {"name": "Research Required", "title": "Director / Founder",
         "email": "info@texasbombers.com", "linkedin": "",
         "source": "texasbombers.com (Gold 18U/16U uses Ryzer)"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit register.ryzer.com (Texas Bombers)"},
    ],
    "Georgia Impact": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@georgiaimpact.com", "linkedin": "",
         "source": "georgiaimpact.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit georgiaimpact.sportngin.com"},
    ],
    "Beverly Bandits Softball": [
        {"name": "Bill Conroy",       "title": "Founder / Program Director",
         "email": "info@thebeverlybandits.com", "linkedin": "",
         "source": "thebeverlybandits.com (founded 1995/1999 travel)"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit thebeverlybandits.com/contact-us/"},
    ],
    "Texas Glory": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@texasglory.com", "linkedin": "",
         "source": "texasglory.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit txglory.sportngin.com"},
    ],
    "Firecrackers Softball": [
        {"name": "Research Required", "title": "National Director / Founder",
         "email": "info@firecrackersoftball.com", "linkedin": "",
         "source": "firecrackersoftball.com (national brand, multiple chapters)"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit firecrackersoftball.sportngin.com"},
    ],
    "East Cobb Bullets": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@eastcobbbullets.com", "linkedin": "",
         "source": "eastcobbbullets.com"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit eastcobbbullets.sportngin.com"},
    ],
    "Corona Angels": [
        {"name": "Research Required", "title": "Founder / Director",
         "email": "info@coronaangels.com", "linkedin": "",
         "source": "coronaangels.com (SoCal PGF-affiliated)"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit coronaangels.sportngin.com"},
    ],
    "OC Batbusters": [
        {"name": "Joe Grubbs",       "title": "Founder / Director",
         "email": "ocbathletics@gmail.com", "linkedin": "",
         "source": "ocbatbusters.com (founded 1979, 30+ national championships)"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Visit ocbatbusters.com/contact"},
    ],
    "Carolina Chaos Softball": [
        {"name": "Research Required", "title": "Founder / Director",
         "email": "", "linkedin": "",
         "source": "carolinachaos.org — platform/contact unconfirmed"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Manual research required"},
    ],
    "Ohio Outlaws Fastpitch": [
        {"name": "Research Required", "title": "Founder / Director",
         "email": "", "linkedin": "",
         "source": "ohiooutlaws.com — platform/contact unconfirmed"},
        {"name": "Research Required", "title": "Club Administrator",
         "email": "", "linkedin": "",
         "source": "Manual research required"},
    ],

    # ── SWIMMING ──────────────────────────────────────────────────────────────
    "PASA (Palo Alto Stanford Aquatics)": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@pausd.org", "linkedin": "",
         "source": "pasa.sportngin.com (nationally elite, multiple Olympians)"},
        {"name": "Research Required", "title": "Head Coach / Program Director",
         "email": "", "linkedin": "",
         "source": "Visit pasa.sportngin.com"},
    ],
    "Nation's Capital Swim Club (NCAP)": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@ncapswim.com", "linkedin": "",
         "source": "ncapswim.com (TeamUnify/GoMotion platform)"},
        {"name": "Research Required", "title": "Head Coach",
         "email": "", "linkedin": "",
         "source": "Visit gomotionapp.com/team/pvncs"},
    ],
    "Badger Swim Club": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@badgerswimsport.com", "linkedin": "",
         "source": "badgerswimsport.com (TeamUnify/GoMotion)"},
        {"name": "Research Required", "title": "Head Coach",
         "email": "", "linkedin": "",
         "source": "Visit gomotionapp.com/team/mrbsc"},
    ],
    "Mission Viejo Nadadores": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@mvnadadores.org", "linkedin": "",
         "source": "mvnadadores.org (Olympic-level club, TeamUnify)"},
        {"name": "Research Required", "title": "Head Coach",
         "email": "", "linkedin": "",
         "source": "Visit gomotionapp.com/team/scmvnm"},
    ],
    "Phoenix Swim Club": [
        {"name": "Research Required", "title": "Executive Director",
         "email": "info@phoenixswimclub.org", "linkedin": "",
         "source": "phoenixswimclub.org (TeamUnify/SportsEngine Motion)"},
        {"name": "Research Required", "title": "Head Coach",
         "email": "", "linkedin": "",
         "source": "Visit gomotionapp.com/team/azbest"},
    ],
}


# ── Outreach templates ─────────────────────────────────────────────────────────

def first_name(full_name: str) -> str:
    if not full_name or full_name == "Research Required":
        return "there"
    return full_name.split()[0]


def get_platform_bucket(platform: str) -> str:
    p = str(platform or "").lower()
    if "sportsengine" in p or "sportngin" in p:
        return "sportsengine"
    if "leagueapps" in p:
        return "leagueapps"
    if "crossbar" in p:
        return "crossbar"
    if "teamunify" in p or "gomotion" in p:
        return "teamunify"
    if "playmetrics" in p:
        return "playmetrics"
    if "demosphere" in p or "otto" in p:
        return "demosphere"
    if "stack sports" in p or "gotsport" in p:
        return "stack"
    if "ryzer" in p:
        return "ryzer"
    if "daysmart" in p:
        return "daysmart"
    return "diy"  # custom / unknown / DIY


def generate_email(program_name: str, contact: dict, sport: str, platform: str,
                   tier: int, region: str) -> tuple[str, str]:
    fname = first_name(contact["name"])
    bucket = get_platform_bucket(platform)

    if tier == 1:
        subject = f"Quick question about {program_name}'s registration setup"
        body = (
            f"Hi {fname},\n\n"
            f"I came across {program_name} while mapping top {sport} programs in {region} — "
            f"impressive what you've built. I noticed you're handling registration and payments "
            f"through a custom setup, which usually means you've outgrown what the off-the-shelf "
            f"platforms offer.\n\n"
            f"We work with programs like yours to modernize payment collection — better parent UX, "
            f"faster reconciliation, lower processing fees — without disrupting what's already working. "
            f"No platform lock-in, no long-term contracts.\n\n"
            f"Would 15 minutes this week make sense? Happy to show you what it looks like for a "
            f"program at {program_name}'s level.\n\n"
            f"Best,\n[Your Name]\n[Company] | [Phone]"
        )
    elif tier == 2 and "crossbar" in bucket:
        subject = f"For {program_name} on Crossbar — a quick thought"
        body = (
            f"Hi {fname},\n\n"
            f"I noticed {program_name} is running on Crossbar — great choice for team management "
            f"and schedules. We work alongside Crossbar with several elite {sport} clubs to handle "
            f"the payment layer specifically: processing fees, failed payments, and manual "
            f"reconciliation are often where clubs feel the most friction.\n\n"
            f"We layer in cleanly without replacing Crossbar for everything it does well. "
            f"Worth 15 minutes to show you how it works for a club your size?\n\n"
            f"Best,\n[Your Name]\n[Company] | [Phone]"
        )
    elif bucket == "sportsengine":
        subject = f"Payment fees for {program_name} on SportsEngine — worth a look"
        body = (
            f"Hi {fname},\n\n"
            f"{program_name}'s reputation in {sport} speaks for itself. I'm reaching out because "
            f"clubs your size on SportsEngine typically absorb 2.9–3.5% on every transaction in "
            f"processing fees — we've helped similar programs cut that meaningfully while keeping "
            f"the registration experience families already know.\n\n"
            f"Would a 15-minute call be worth it to see the numbers?\n\n"
            f"Best,\n[Your Name]\n[Company] | [Phone]"
        )
    elif bucket == "leagueapps":
        subject = f"A note for {program_name} on LeagueApps payment costs"
        body = (
            f"Hi {fname},\n\n"
            f"{program_name} is one of the top {sport} programs in the country. We work with "
            f"several LeagueApps clubs to reduce per-transaction payment costs and improve the "
            f"family payment experience — without replacing LeagueApps for everything it does well.\n\n"
            f"Happy to share specific numbers in 15 minutes.\n\n"
            f"Best,\n[Your Name]\n[Company] | [Phone]"
        )
    elif bucket == "teamunify":
        subject = f"Payment modernization for {program_name} on TeamUnify / GoMotion"
        body = (
            f"Hi {fname},\n\n"
            f"{program_name} is an elite club — the GoMotion/TeamUnify infrastructure works well "
            f"for scheduling and roster management, but the payment layer often leaves money on the "
            f"table in processing fees and failed-payment churn.\n\n"
            f"We've helped similar aquatics programs recover meaningful revenue. Worth a 15-minute "
            f"conversation?\n\n"
            f"Best,\n[Your Name]\n[Company] | [Phone]"
        )
    else:
        subject = f"Payment optimization question for {program_name}"
        body = (
            f"Hi {fname},\n\n"
            f"I admire what {program_name} has built in the {sport} space. I'm reaching out because "
            f"we've helped similar programs reduce payment processing overhead and improve collection "
            f"rates — often without changing the registration workflow families already use.\n\n"
            f"Would 15 minutes make sense to explore?\n\n"
            f"Best,\n[Your Name]\n[Company] | [Phone]"
        )
    return subject, body


def generate_linkedin_dm(program_name: str, contact: dict, sport: str,
                          platform: str, tier: int, region: str) -> str:
    fname = first_name(contact["name"])
    if tier == 1:
        return (
            f"Hi {fname} — I came across {program_name} while researching elite {sport} programs "
            f"in {region}. Quick question: have you explored alternatives to your current payment/"
            f"registration setup? We work with similar clubs and typically save them time and money "
            f"without disrupting what's already working. Worth a quick 15-min chat?"
        )
    elif tier == 2:
        return (
            f"Hi {fname} — noticed {program_name} is on Crossbar. We work with several Crossbar "
            f"{sport} clubs to reduce the payment friction layer (fees, failed cards, reconciliation). "
            f"Would a quick 15-min call be worth it?"
        )
    else:
        return (
            f"Hi {fname} — {program_name} is one of the top {sport} programs in the country. "
            f"I work with similar clubs on reducing payment processing costs and improving family "
            f"payment experience. Would a quick 15-minute conversation make sense?"
        )


# ── Region inference ───────────────────────────────────────────────────────────
REGION_MAP = {
    "Chicago": "Midwest", "Illinois": "Midwest", "Michigan": "Midwest",
    "Ohio": "Midwest", "Indiana": "Midwest", "Missouri": "Midwest",
    "Minnesota": "Midwest", "Wisconsin": "Midwest", "Iowa": "Midwest",
    "Kansas": "Midwest", "Nebraska": "Midwest", "St. Louis": "Midwest",
    "Detroit": "Midwest", "Columbus": "Midwest", "Milwaukee": "Midwest",
    "New York": "Northeast", "NJ": "Northeast", "New Jersey": "Northeast",
    "Boston": "Northeast", "Connecticut": "Northeast", "Massachusetts": "Northeast",
    "New England": "Northeast", "Pennsylvania": "Northeast", "Maryland": "Mid-Atlantic",
    "DC": "Mid-Atlantic", "Virginia": "Mid-Atlantic", "Delaware": "Mid-Atlantic",
    "Texas": "South", "Georgia": "Southeast", "Florida": "Southeast",
    "Atlanta": "Southeast", "Carolina": "Southeast", "Tennessee": "Southeast",
    "Nashville": "Southeast", "Charlotte": "Southeast",
    "California": "West", "Los Angeles": "West", "San Jose": "West",
    "Orange County": "West", "San Diego": "West", "Phoenix": "West",
    "Arizona": "West", "Oregon": "Northwest", "Seattle": "Northwest",
    "Washington": "Northwest", "Colorado": "Mountain West", "Denver": "Mountain West",
    "Utah": "Mountain West", "Nevada": "Mountain West",
    "Dallas": "South", "Houston": "South", "Pittsburgh": "Mid-Atlantic",
    "Buffalo": "Northeast", "Omaha": "Midwest",
}

PROGRAM_REGION = {
    "Chicago Mission AAA": "Midwest", "Buffalo Jr. Sabres": "Northeast",
    "Little Caesars AAA Hockey": "Midwest", "Boston Jr. Bruins": "Northeast",
    "New Jersey Rockets": "Northeast", "Connecticut Polar Bears": "Northeast",
    "Omaha AAA Hockey": "Midwest", "St. Louis Blues Elite Hockey": "Midwest",
    "Shattuck-St. Mary's Hockey": "Midwest", "Team Illinois Hockey": "Midwest",
    "North Jersey Avalanche": "Northeast", "Western Mass Warriors": "Northeast",
    "Honeybaked Hockey": "Midwest", "Tri-City Storm": "Midwest",
    "Colorado Thunderbirds": "Mountain West", "Pittsburgh Penguins Elite": "Mid-Atlantic",
    "Detroit Compuware": "Midwest", "Dallas Stars Elite": "South",
    "Carolina Jr. Hurricanes": "Southeast", "Green Bay Jr. Gamblers": "Midwest",
    "Nashville Jr. Predators": "Southeast", "Phoenix Jr. Coyotes": "Southwest",
    "Minnesota Wild Youth": "Midwest", "Los Angeles Jr. Kings": "West",
    "San Jose Jr. Sharks": "West",
    "Canes Baseball": "Southeast", "EvoShield Canes (Southeast)": "Southeast",
    "Canes Midwest": "Midwest", "East Cobb Baseball": "Southeast",
    "Texas Baseball Ranch": "South", "Perfect Game (PGBA)": "Midwest",
    "Area Codes Baseball": "National", "ExtraInnings Baseball": "National",
    "Elite Baseball of Lemont": "Midwest", "Baseball Youth": "Mid-Atlantic",
    "Diamond Sports": "National", "Baseball Factory": "National",
    "Future Stars Series": "National", "USSSA Baseball": "National",
    "Select Baseball": "Midwest", "New England Ruffnecks": "Northeast",
    "Texas Bombers Baseball": "South", "D-BAT Academies": "National",
    "Team One Baseball": "National", "Ripken Baseball": "Mid-Atlantic",
    "Five Tool Baseball": "Southeast", "Prep Baseball Report (PBR)": "National",
    "USA Baseball Youth Events": "National", "Mid-South Baseball": "Southeast",
    "Power Baseball": "National",
    "Solar SC": "South", "Surf Soccer Club": "West", "FC Dallas Youth": "South",
    "NCFC Youth": "Southeast", "Eclipse Select SC": "Midwest", "PDA Soccer": "Northeast",
    "LA Galaxy Academy": "West", "Concorde Fire": "Southeast",
    "Houston Dash Academy": "South", "Sporting KC Academy": "Midwest",
    "RSL Arizona": "Southwest", "Michigan Hawks": "Midwest",
    "Sockers FC Chicago": "Midwest", "Ohio Premier Soccer": "Midwest",
    "GPS Massachusetts": "Northeast", "Weston FC": "Southeast",
    "Beach FC": "Mid-Atlantic", "Crossfire Premier": "Northwest",
    "Florida Premier FC": "Southeast", "FC Stars Massachusetts": "Northeast",
    "St. Louis Scott Gallagher": "Midwest", "Heat FC (San Diego)": "West",
    "Albion SC": "West", "Charlotte Soccer Academy": "Southeast",
    "Tampa Bay United": "Southeast",
    "Team Takeover": "Mid-Atlantic", "Brad Beal Elite": "Midwest",
    "Oakland Soldiers": "West", "Mokan Elite": "Midwest",
    "PSA Cardinals": "Northeast", "All In Elite": "Mid-Atlantic",
    "Team Penny": "Southeast", "NY Rens": "Northeast",
    "Nightrydas Elite": "Southeast", "Howard Pulley Panthers": "Midwest",
    "Expressions Elite": "Mid-Atlantic", "Drive Nation": "South",
    "Mass Rivals": "Northeast", "King James Shooting Stars": "Midwest",
    "Georgia Stars": "Southeast", "Texas Titans": "South",
    "Colorado Hawks": "Mountain West", "New England Playmakers": "Northeast",
    "Team Texas": "South", "Philly Pride": "Mid-Atlantic",
    "Houston Defenders": "South", "Dream Vision NY": "Northeast",
    "Indiana Elite": "Midwest", "Oregon Nike Elite": "Northwest",
    "Seattle Rotary": "Northwest",
    "3d Lacrosse": "National", "True Lacrosse": "National",
    "Predators Lacrosse": "Mid-Atlantic", "Leading Edge Lacrosse": "Northeast",
    "Laxachusetts": "Northeast", "MadLax": "Mid-Atlantic",
    "Chesapeake Bayhawks Youth": "Mid-Atlantic", "Trilogy Lacrosse": "Mid-Atlantic",
    "Express Lacrosse": "Northeast", "Annapolis Hawks": "Mid-Atlantic",
    "Crabs Lacrosse": "Mid-Atlantic", "Sweetlax Florida": "Southeast",
    "Atlas Lacrosse Club": "Northeast", "Lax Factory": "Mid-Atlantic",
    "DC Express Lacrosse": "Mid-Atlantic", "Pride Lacrosse New England": "Northeast",
    "Ultimate Lacrosse": "Mid-Atlantic", "CT Hammerheads": "Northeast",
    "Big 4 Lacrosse": "Mid-Atlantic", "Carolina LAX": "Southeast",
    "A5 Volleyball": "Southeast", "Munciana Volleyball": "Midwest",
    "Colorado Fusion VBC": "Mountain West", "Long Beach Volleyball Club": "West",
    "Elevate Volleyball": "Northwest", "KIVA Volleyball": "Midwest",
    "Beverly Bandits VB": "Midwest", "Club Gold Volleyball (TX)": "South",
    "Sports Performance VBC": "West", "Crossroads of America VBC": "Midwest",
    "Club K Volleyball": "National", "Great Plains Region Volleyball": "Midwest",
    "Illinois Valley Juniors VBC": "Midwest", "NOVA Volleyball": "Mid-Atlantic",
    "Rox Volleyball": "National",
    "Texas Bombers Gold": "South", "Georgia Impact": "Southeast",
    "Beverly Bandits Softball": "Midwest", "Texas Glory": "South",
    "Firecrackers Softball": "West", "East Cobb Bullets": "Southeast",
    "Corona Angels": "West", "OC Batbusters": "West",
    "Carolina Chaos Softball": "Southeast", "Ohio Outlaws Fastpitch": "Midwest",
    "PASA (Palo Alto Stanford Aquatics)": "West",
    "Nation's Capital Swim Club (NCAP)": "Mid-Atlantic",
    "Badger Swim Club": "Midwest", "Mission Viejo Nadadores": "West",
    "Phoenix Swim Club": "Southwest",
}


# ── Main ───────────────────────────────────────────────────────────────────────

def load_programs():
    programs = []
    for csv_file in [
        DATA_DIR / "club_sports_payment_platforms.csv",
        DATA_DIR / "club_sports_payment_platforms_100more.csv",
    ]:
        with open(csv_file, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                programs.append(row)
    return programs


FIELDNAMES = [
    "sport", "program", "homepage", "platform_detected",
    "lead_tier", "tier_rationale", "tpv_min_k", "tpv_max_k", "region",
    "contact_rank", "contact_name", "contact_title",
    "contact_email", "contact_linkedin", "contact_source",
    "outreach_channel", "email_subject", "outreach_body",
]


def build_rows(programs: list) -> list[dict]:
    rows = []
    for p in programs:
        name     = p["program"]
        sport    = p["sport"]
        platform = p.get("platform_detected", "") or ""
        homepage = p.get("homepage", "")
        tier     = score_tier(platform)
        rationale = tier_rationale(platform, tier)
        tpv_min, tpv_max = TPV.get(sport, (50, 300))
        region   = PROGRAM_REGION.get(name, "National")
        contacts = CONTACTS_DB.get(name, [
            {"name": "Research Required", "title": "Executive Director / Director",
             "email": "", "linkedin": "", "source": f"Visit {homepage}/staff"},
            {"name": "Research Required", "title": "Club Administrator",
             "email": "", "linkedin": "", "source": f"Visit {homepage}/contact"},
        ])

        for rank, contact in enumerate(contacts[:2], start=1):
            subject, body = generate_email(name, contact, sport, platform, tier, region)
            linkedin_dm   = generate_linkedin_dm(name, contact, sport, platform, tier, region)
            has_email     = bool(contact.get("email") and contact["name"] != "Research Required")
            channel       = "email" if has_email else "linkedin"
            rows.append({
                "sport": sport,
                "program": name,
                "homepage": homepage,
                "platform_detected": platform,
                "lead_tier": tier,
                "tier_rationale": rationale,
                "tpv_min_k": tpv_min,
                "tpv_max_k": tpv_max,
                "region": region,
                "contact_rank": rank,
                "contact_name": contact["name"],
                "contact_title": contact["title"],
                "contact_email": contact.get("email", ""),
                "contact_linkedin": contact.get("linkedin", ""),
                "contact_source": contact.get("source", ""),
                "outreach_channel": channel,
                "email_subject": subject,
                "outreach_body": body if channel == "email" else linkedin_dm,
            })
    return rows


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def generate_report(rows: list[dict], out_path: Path):
    today = date.today().isoformat()
    tier1 = [r for r in rows if r["lead_tier"] == 1 and r["contact_rank"] == 1]
    tier2 = [r for r in rows if r["lead_tier"] == 2 and r["contact_rank"] == 1]
    tier3 = [r for r in rows if r["lead_tier"] == 3 and r["contact_rank"] == 1]

    # Deduplicate by program for counts
    programs = {r["program"] for r in rows}
    t1_progs = {r["program"] for r in rows if r["lead_tier"] == 1}
    t2_progs = {r["program"] for r in rows if r["lead_tier"] == 2}
    t3_progs = {r["program"] for r in rows if r["lead_tier"] == 3}

    # Top 10 Tier 1 by TPV midpoint
    t1_sorted = sorted(
        [r for r in rows if r["lead_tier"] == 1 and r["contact_rank"] == 1],
        key=lambda r: -(r["tpv_min_k"] + r["tpv_max_k"]),
    )
    top10 = t1_sorted[:10]

    # Platform breakdown (contact_rank==1 only)
    from collections import Counter
    platform_counts = Counter()
    for r in rows:
        if r["contact_rank"] == 1:
            p = str(r["platform_detected"] or "").lower()
            if "sportsengine" in p or "sportngin" in p:
                platform_counts["SportsEngine"] += 1
            elif "leagueapps" in p:
                platform_counts["LeagueApps"] += 1
            elif "crossbar" in p:
                platform_counts["Crossbar"] += 1
            elif "teamunify" in p or "gomotion" in p:
                platform_counts["TeamUnify / GoMotion"] += 1
            elif "playmetrics" in p:
                platform_counts["PlayMetrics"] += 1
            elif "stack sports" in p:
                platform_counts["Stack Sports"] += 1
            elif "demosphere" in p or "otto" in p:
                platform_counts["Demosphere / OTTO"] += 1
            elif "ryzer" in p:
                platform_counts["Ryzer"] += 1
            elif "daysmart" in p:
                platform_counts["DaySmart"] += 1
            elif "paypal" in p:
                platform_counts["PayPal (direct)"] += 1
            elif "square" in p:
                platform_counts["Square"] += 1
            else:
                platform_counts["Unknown / Custom"] += 1

    lines = [
        f"# Youth Club Sports — Outreach Summary Report",
        f"",
        f"**Generated:** {today}  ",
        f"**Total programs:** {len(programs)}  ",
        f"**Total contact rows:** {len(rows)}",
        f"",
        f"---",
        f"",
        f"## Lead Tier Summary",
        f"",
        f"| Tier | Programs | Description | Action |",
        f"|------|----------|-------------|--------|",
        f"| **Tier 1** | {len(t1_progs)} | DIY / Custom / Unknown platform | Outreach immediately |",
        f"| **Tier 2** | {len(t2_progs)} | Small platforms (Crossbar, etc.) | Outreach this quarter |",
        f"| **Tier 3** | {len(t3_progs)} | Entrenched (SportsEngine, LeagueApps…) | Nurture / long-term |",
        f"",
        f"---",
        f"",
        f"## Platform Distribution (150 programs)",
        f"",
        f"| Platform | Programs |",
        f"|----------|----------|",
    ]
    for plat, cnt in platform_counts.most_common():
        lines.append(f"| {plat} | {cnt} |")

    lines += [
        f"",
        f"---",
        f"",
        f"## Top 10 Priority Targets (Tier 1, sorted by estimated TPV)",
        f"",
        f"| # | Sport | Program | Platform | Est. TPV | Primary Contact | Email/LinkedIn |",
        f"|---|-------|---------|----------|----------|-----------------|----------------|",
    ]
    for i, r in enumerate(top10, 1):
        tpv_str = f"${r['tpv_min_k']}K–${r['tpv_max_k']}K"
        email = r["contact_email"] or r["contact_linkedin"] or "research required"
        lines.append(
            f"| {i} | {r['sport']} | **{r['program']}** | {r['platform_detected'] or 'Unknown'} "
            f"| {tpv_str} | {r['contact_name']} ({r['contact_title']}) | {email} |"
        )

    lines += [
        f"",
        f"---",
        f"",
        f"## Top 5 Copy-Paste Outreach (Tier 1)",
        f"",
    ]
    for r in top10[:5]:
        lines += [
            f"### {r['program']} — {r['contact_name']}",
            f"**Channel:** {r['outreach_channel'].upper()}  ",
            f"**To:** {r['contact_email'] or r['contact_linkedin'] or 'TBD'}  ",
            f"**Subject:** {r['email_subject']}",
            f"",
            f"```",
            r["outreach_body"],
            f"```",
            f"",
        ]

    lines += [
        f"---",
        f"",
        f"## Tier 2 Programs (Crossbar — Upgrade Opportunity)",
        f"",
        f"| Program | Sport | Region | Primary Contact | Email |",
        f"|---------|-------|--------|-----------------|-------|",
    ]
    for r in tier2:
        email = r["contact_email"] or "—"
        lines.append(
            f"| {r['program']} | {r['sport']} | {r['region']} "
            f"| {r['contact_name']} | {email} |"
        )

    lines += [
        f"",
        f"---",
        f"",
        f"## Contacts Requiring Manual Research",
        f"",
        f"The following programs have no confirmed decision-maker contact. "
        f"Recommended action: visit their staff/about page or use Hunter.io domain search.",
        f"",
        f"| Program | Sport | Homepage | Tier |",
        f"|---------|-------|----------|------|",
    ]
    for r in rows:
        if r["contact_rank"] == 1 and r["contact_name"] == "Research Required":
            lines.append(
                f"| {r['program']} | {r['sport']} | {r['homepage']} | {r['lead_tier']} |"
            )

    lines += [
        f"",
        f"---",
        f"",
        f"## Sport TPV Reference Ranges",
        f"",
        f"| Sport | Annual TPV Range (per club) | Notes |",
        f"|-------|---------------------------|-------|",
        f"| Hockey | $100K–$750K | Highest TPV; elite AAA clubs $500K+ |",
        f"| Baseball | $75K–$600K | Large showcase orgs $400K+ |",
        f"| Swimming | $60K–$450K | Elite clubs $300K+ |",
        f"| Soccer | $50K–$500K | ECNL/MLS Next clubs $300K+ |",
        f"| Softball | $50K–$400K | National PGF programs $300K+ |",
        f"| Lacrosse | $60K–$400K | Mid-Atlantic elite clubs $250K+ |",
        f"| Volleyball | $40K–$350K | AVCA elite clubs $200K+ |",
        f"| Basketball | $30K–$200K | AAU programs $100K+ |",
        f"",
        f"---",
        f"*Report generated by compile_outreach.py*",
    ]

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    programs = load_programs()
    print(f"Loaded {len(programs)} programs from CSVs")

    rows = build_rows(programs)
    print(f"Generated {len(rows)} contact rows")

    # 1. Full contacts CSV
    out_all = DATA_DIR / "contacts_and_outreach.csv"
    write_csv(out_all, rows, FIELDNAMES)
    print(f"Wrote {out_all}")

    # 2. Tier 1 priority CSV (sorted by TPV desc)
    tier1_rows = [r for r in rows if r["lead_tier"] == 1]
    tier1_rows.sort(key=lambda r: -(r["tpv_min_k"] + r["tpv_max_k"]))
    out_t1 = DATA_DIR / "tier1_priority_outreach.csv"
    write_csv(out_t1, tier1_rows, FIELDNAMES)
    print(f"Wrote {out_t1} ({len(tier1_rows)} rows)")

    # 3. Summary report
    out_rpt = REPORTS_DIR / "outreach_summary_report.md"
    generate_report(rows, out_rpt)
    print(f"Wrote {out_rpt}")

    # Stats
    from collections import Counter
    tier_dist = Counter(r["lead_tier"] for r in rows if r["contact_rank"] == 1)
    print(f"\nTier distribution (unique programs):")
    for t in [1, 2, 3]:
        print(f"  Tier {t}: {tier_dist[t]} programs")


if __name__ == "__main__":
    main()
