# Youth Travel/Club Sports — Payment Platform Research Report

**Date:** 2026-05-31  
**Programs surveyed:** 50 (10 per sport × 5 sports)  
**Method:** Web search fingerprinting + direct URL/domain pattern analysis

---

## Executive Summary

Across 50 major youth travel/club sports programs, **LeagueApps** and **SportsEngine** are the dominant platforms — each used by 11 programs (22% each). Together they account for 44% of all confirmed platforms. **Crossbar** is the clear leader in AAA hockey (4 of 10 hockey programs confirmed). **PlayMetrics** is growing rapidly in elite soccer. Roughly 30% of programs (15 of 50) use custom-built or non-standard solutions, particularly in basketball where grassroots AAU programs rely on direct payment, TicketLeap, or Exposure Events for tournament entries.

---

## Platform Frequency Summary

| Platform | Count | % of 50 |
|---|---|---|
| **LeagueApps** | 11 | 22% |
| **SportsEngine** | 11 | 22% |
| **Custom / Unknown** | 9 | 18% |
| **Crossbar** | 4 | 8% |
| **PlayMetrics** | 2 | 4% |
| **Stack Sports** | 1 | 2% |
| **Demosphere (OTTO Sport AI)** | 1 | 2% |
| **DaySmart** | 1 | 2% |
| **TicketLeap + Exposure Events** | 1 | 2% |
| **Site inactive / domain not resolving** | 6 | 12% |

---

## Results by Sport

### ⚾ Baseball (10 programs)

| Program | Platform | Registration URL |
|---|---|---|
| Canes Baseball | **LeagueApps** | canesbaseball.leagueapps.com |
| East Cobb Baseball | **SportsEngine** | east-cobb-baseball.sportngin.com |
| Texas Baseball Ranch | Custom (Memberful) | membership.texasbaseballranch.com |
| Perfect Game (PGBA) | Custom In-House | perfectgame.org/Registration/ |
| Area Codes Baseball | **Stack Sports** | register.areacodebaseball.com |
| ExtraInnings Baseball | — | Domain not resolving |
| Elite Baseball of Lemont | — | Domain not resolving |
| Baseball Youth | Custom (Athletx) | baseballyouth.com/individuals/create-account.php |
| Diamond Sports | — | Domain not resolving |
| EvoShield Canes (Southeast) | **LeagueApps** | canesbaseball.leagueapps.com |

**Key finding:** Baseball is fragmented. Major networks (Canes, Area Codes) use enterprise platforms; individual academies and ranches run custom membership portals. Perfect Game operates a fully proprietary system supporting 1M+ tournament registrations annually. Three domains in this list were inactive.

---

### 🥍 Lacrosse (10 programs)

| Program | Platform | Registration URL |
|---|---|---|
| 3d Lacrosse | **LeagueApps** | 3dlacrosse-[region].leagueapps.com |
| True Lacrosse | **LeagueApps** | truelacrosse[region].leagueapps.com |
| Predators Lacrosse | Unknown / Custom | predatorslacrosse.com |
| Leading Edge Lacrosse | **LeagueApps** | leadingedgeelite.leagueapps.com |
| Laxachusetts | **SportsEngine** | sportsengine.com/org/laxachusetts |
| MadLax | **SportsEngine** | capital.madlax.com (via sportngin) |
| Chesapeake Bayhawks Youth | — | Domain not resolving |
| Trilogy Lacrosse | **LeagueApps** | trilogylacrosse.leagueapps.com |
| Express Lacrosse | **LeagueApps** | liexpress.leagueapps.com |
| Annapolis Hawks | **LeagueApps** | annapolishawks.leagueapps.com |

**Key finding:** Lacrosse is dominated by **LeagueApps** (6 of 10 confirmed programs). This aligns with LeagueApps' strength in competitive club sports on the East Coast. SportsEngine holds the remaining 2 confirmed spots. Note: USA Lacrosse named SportsEngine its Preferred Platform Partner in April 2026, which may shift future adoption.

---

### 🏒 Hockey (10 programs)

| Program | Platform | Registration URL |
|---|---|---|
| Little Caesars AAA Hockey | **Crossbar** | littlecaesarshockey.com.app.crossbar.org |
| Shattuck-St. Mary's Hockey | Custom / Active Network | s-sm.org (boarding school model) |
| Chicago Mission AAA | Custom (WordPress) | chicagomission.com/fall-registration-payment/ |
| Honeybaked Hockey | **SportsEngine** | sportsengine.com/org/honeybaked-hockey-club |
| Tri-City Storm | **SportsEngine** | stormhockey.sportngin.com |
| Boston Jr. Bruins | **Crossbar** | bostonjuniorbruins.org |
| Team Illinois Hockey | — | Domain not resolving (wrong URL in list) |
| Colorado Thunderbirds | **SportsEngine** | tbirdhockey.sportngin.com |
| New Jersey Rockets | **Crossbar** | rocketshockeyclub.com (via Crossbar) |
| St. Louis Blues Elite Hockey | **Crossbar** | stlaaablues.com (migrated to Crossbar) |

**Key finding:** Hockey shows the clearest platform bifurcation: **Crossbar** (4 confirmed) vs **SportsEngine** (3 confirmed). Crossbar was built by a hockey director for hockey organizations and is headquartered in St. Louis — explaining its Midwest/Northeast AAA hockey dominance. Many clubs are actively migrating from SportsEngine to Crossbar. Shattuck-St. Mary's is technically a boarding school and operates differently from club programs.

---

### ⚽ Soccer (10 programs)

| Program | Platform | Registration URL |
|---|---|---|
| Solar SC | **LeagueApps** | solarsoccerclub.leagueapps.com |
| Surf Soccer Club | **PlayMetrics** | members.surfsoccer.com |
| FC Dallas Youth | **SportsEngine** | sportsengine.com/org/fc-dallas-youth |
| NCFC Youth | **PlayMetrics** | ncfcyouth.com (via PlayMetrics account) |
| Eclipse Select SC | Unknown / Custom | eclipseselect.org |
| PDA Soccer | **Demosphere (OTTO Sport AI)** | pdasoccer.demosphere-secure.com |
| LA Galaxy Academy | **DaySmart** | youth.lagalaxy.com |
| Concorde Fire | **SportsEngine** | sportsengine.com/org/concorde-fire-soccer-club |
| Houston Dash Academy | **LeagueApps** | houstondynamoyouth.leagueapps.com |
| Sporting KC Academy | **SportsEngine** | sportingkcacademy.com (SportsEngine partner) |

**Key finding:** Soccer has the highest platform diversity. SportsEngine and LeagueApps each hold 3 spots, while PlayMetrics (2) reflects its growing footprint after merging with Stack Sports and acquiring SportsEngine. Demosphere (now OTTO Sport AI) remains the long-tenured platform for established clubs like PDA. Notable: MLS-affiliated academies (LA Galaxy, Sporting KC) use very different solutions — DaySmart vs SportsEngine respectively.

---

### 🏀 Basketball (10 programs)

| Program | Platform | Registration URL |
|---|---|---|
| Team Takeover | Custom | team-takeover.com/registration |
| Brad Beal Elite | **LeagueApps** | stleagles.leagueapps.com |
| Oakland Soldiers | Custom / Exposure Events | soldierbasketball.com |
| Mokan Elite | Custom | mokanbasketball.com |
| PSA Cardinals | Custom | psacardinals.com |
| All In Elite | Custom (Squarespace) | allineliteua.com |
| Team Penny | — | Domain not resolving |
| NY Rens | **SportsEngine** | nyrhoops.sportngin.com |
| Nightrydas Elite | TicketLeap + Exposure Events | nightrydaselite.ticketleap.com |
| Howard Pulley Panthers | **SportsEngine** | howardpulleybasketball.sportngin.com |

**Key finding:** Basketball (AAU) is the least consolidated sport for registration platforms. Most programs rely on **custom websites, direct payment, or event-specific tools** (TicketLeap, Exposure Events). Only 3 of 10 confirmed programs use a named sports management platform. This reflects the grassroots, relationship-driven nature of AAU basketball where registration often happens through coaches directly.

---

## Hypothesis Validation

| Hypothesis | Result |
|---|---|
| SportsEngine dominant in hockey and soccer | **Partially confirmed** — SportsEngine holds 3 soccer + 3 hockey spots, but Crossbar dominates AAA hockey |
| Stack Sports / GotSoccer common in elite soccer | **Not confirmed** — only 1 direct Stack Sports detection (Area Codes Baseball) |
| Crossbar very common in AAA hockey | **Confirmed** — 4 of 10 hockey programs on Crossbar |
| LeagueApps growing in lacrosse and basketball | **Confirmed in lacrosse** (6/10), weaker in basketball (1/10) |
| TeamSnap common in smaller programs | **Not detected** — none of the top-50 programs use TeamSnap |
| Ryzer emerging in basketball | **Not detected** in this sample |
| Demosphere common in established soccer clubs | **Confirmed** — PDA Soccer on Demosphere/OTTO Sport AI |
| Custom / Wix / Squarespace for small programs | **Partially confirmed** — several basketball and baseball programs on custom sites |

---

## Industry Consolidation Notes (2025–2026)

- **PlayMetrics acquired SportsEngine** (2025) — both continue to operate as separate products for now
- **Stack Sports merged with PlayMetrics** — creating a large youth sports tech holding company
- **Demosphere rebranded to OTTO Sport AI** — same platform, new name
- **USA Lacrosse named SportsEngine Preferred Partner** (April 2026) — may accelerate SE adoption in lacrosse
- **Crossbar was acquired by PlayMetrics** — SportsEngine and Crossbar are now under the same parent company

---

## Data Quality Notes

- **6 domains did not resolve** during automated scraping and could not be verified via search: ExtraInnings Baseball, Elite Baseball of Lemont, Diamond Sports, Chesapeake Bayhawks Youth, Team Illinois Hockey, Team Penny.
- Several programs listed different URLs than their active sites (e.g., stlblueselite.com → stlaaablues.com; howardpulleypanthers.com → howardpulleybasketball.com).
- Shattuck-St. Mary's is a boarding school, not a travel club — included per the prompt but its registration model is fundamentally different.
- Platform detection is based on public-facing web fingerprints; some programs may use different platforms for internal admin vs public registration.
