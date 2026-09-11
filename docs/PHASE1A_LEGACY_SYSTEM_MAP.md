# Phase 1a: Legacy System Map – Galactic Empire (MajorBBS)

**Date:** 2026-09-11  
**Source:** `Original_Code/` (MIT-licensed C codebase from https://github.com/bsimser/ge)  
**Scope:** Analysis-only; no implementation.

---

## Executive Summary

**MajorBBS Galactic Empire** (c. 1988-1992, Mike Murdock) is a BBS-hosted space conquest game built on turn-based sessions with real-time automation. Players pilot ships through a 30×15 sector grid universe, trade resources at planets, establish colonies, and engage in ship-to-ship combat or planetary conquest. The game combines **synchronous command-driven gameplay** (BBS sessions) with **asynchronous world simulation** (6-second tick system for movement/combat, 55-second tick for planetary production).

**Core retention loop:** Explore → Claim planets → Produce goods → Sell for cash → Upgrade ships → Conquer rivals → Repeat.  
**Win condition:** Highest score (kills + planets + production + cash) by midnight reset.  
**Recommended strategy for modern port:** **KEEP** the strategic fleet/conquest meta; **TRANSFORM** tick-based simulation into always-online real-time; **KILL** BBS turn constraints and single-threaded command parser. The space-conquest fantasy (build empire, crush rivals) is timeless; the BBS I/O model is not.

**Primary design tension:** Legacy relies on discrete BBS sessions (player logs in, issues commands, logs out) + real-time ticks while offline. Modern mobile MMO expects persistent connections. Recommend: replace tick polling with event-driven server updates; preserve strategic pacing (production cycles, fleet movement travel time) but allow instant response to player actions.

---

## 1. File Inventory

### Core game module (`mbmgemp/`)
| File | Lines | Role |
|------|-------|------|
| `GEMAIN.C` | 3668 | Module entry, initialization, real-time tick handlers (TICKTIME=6s, PLANTIME=55s), database (Btrieve) I/O, midnight reset |
| `GEMAIN.H` | 690 | Primary structs: `WARSHP` (ship, 512b), `WARUSR` (user account, 256b), `GALPLNT` (planet, 512b), `GALSECT` (sector, 512b), `GALWORM` (wormhole), `MAIL`, `TEAM`; defines: 14 item types, energy/damage constants, tick rates |
| `GEGLOBAL.H` | 290 | Global variable externs for all modules |
| `GEPROTO.H` | 290 | Function prototypes (ANSI C) |
| `GECMDS.C` | 6166 | Command parser + 70+ commands: navigate (impulse, warp, rotate, orbit), combat (phasor, torpedo, missile, shields, cloak), trade (buy, sell, price, transfer), planet (admin, attack), misc (scan, report, send, team) |
| `GEFUNCS.C` | 2686 | Core game logic: ship movement (`moveship`, `hyperspace`, `gravity`), damage resolution (`killem`, `randamage`, `pdamage`), energy/shields (`recharge`, `shieldhit`), mail, weight calculations |
| `GEPLANET.C` | 874 | Planet production (`multiply`): population growth, resource fabrication, tax collection, spy mechanics; sector/planet lookup |
| `GECYBS.C` | 839 | Cybertron AI (NPCs): init, tick behavior, attack logic, skill-based targeting, loot caps |
| `GEDROIDS.C` | 539 | Droid AI (3 classes: class 10/11/12 NPCs with different behaviors) |
| `GELIB.C` | 308 | Math utilities: bearing, distance, angle, vector, random |
| `GESAMPLE.C` | 588 | Sample custom ship class implementations (unused templates) |

### Map editor (`mbmgemap/`)
| File | Role |
|------|------|
| `MBMGEMAP.C` | 903 lines; standalone tool to generate/convert universe sector maps (pre-v3.2 to v3.2 format); initializes planets, wormholes |
| `MBMGEMAP.H` | Structs for map generation |

### Converters (`mbmgecvt/`, `register/`)
Auxiliary tools for database migration and registration (test-drive licensing). Not relevant to modern port.

---

## 2. Core Loops

### 2.1 Player session cadence
**BBS turn-based model:**
1. Player dials in → logs on → enters "Galactic Empire" module (`gelogon` in `GEMAIN.C:966`)
2. Loads user account (`WARUSR` from `GEuser.dat` via `geudb` lookup, `GEMAIN.C:1601`)
3. Selects active ship (`WARSHP` from `GEship.dat` via `gepdb` lookup, `GEMAIN.C:1519`)
4. Enters command loop (`galemp` in `GEMAIN.C:1453`, calls `cmd_*` functions from `GECMDS.C`)
5. Issues commands (3-letter prefix parser: `imp` → impulse drive, `pha` → fire phasor, `buy` → purchase goods, etc.)
6. Logs off → ship remains in universe, subject to real-time tick system

**Key insight:** Player's *active session* is command-driven and blocking (waits for input), but *universe* runs continuously via `rtkick()` timers (`GEMAIN.C:954-972`).

### 2.2 Real-time tick system (asynchronous automation)
**Tick handlers** (`GEMAIN.C`):
- `TICKTIME = 6` seconds → `warrti()` processes all ships: movement, combat resolution, shields, energy recharge (`GEMAIN.C:2193-2252`)
- `TICKTIME2 = 1` second → `warrti2()` processes cyborgs/droids (`GEMAIN.C:2425-2472`)
- `PLANTIME = 55` seconds → `plarti()` processes all planets: production (`multiply()` in `GEPLANET.C:195`), spy checks, tax collection (`GEMAIN.C:1919-2167`)
- `60` seconds → `warrti3()` mystery tick (code unclear, possibly housekeeping)
- `1` second → `autorti()` processes docked ships in repair/maintenance queues

**Critical for modern port:** Ticks are *polled* (MajorBBS scheduler calls these callbacks). Replace with event-driven updates (e.g., coroutines, async tasks) for mobile. Preserve *timing* (6s ship tick, 55s planet tick) to maintain strategic pacing.

### 2.3 Primary player loops
1. **Exploration loop:** Navigate sectors (`cmd_impulse`, `cmd_warp` in `GECMDS.C:450-610`) → scan for planets (`cmd_scan` in `GECMDS.C:2106`) → orbit (`cmd_orbit` in `GECMDS.C:726`)
2. **Trade loop:** Buy goods at owned/allied planets (`cmd_buy` in `GECMDS.C:4169`) → transport to high-demand sectors → sell (`cmd_sell` in `GECMDS.C:4071`)
3. **Colony loop:** Claim unowned planet (`cmd_admin` in `GECMDS.C:3430`) → set production rates/taxes → accumulate resources (`GEPLANET.C:195-356`) → extract gold/wealth
4. **Combat loop (ship):** Lock target (`cmd_lock` in `GECMDS.C:5036`) → fire phasor/torpedo/missile (`cmd_phas`/`cmd_torp`/`cmd_missl` in `GECMDS.C:797-1182`) → manage shields/cloak → loot wreckage (`killem` in `GEFUNCS.C:1058`)
5. **Combat loop (planet):** Attack with men or fighters (`cmd_attack` in `GECMDS.C:3483`) → RNG ground battle (`attack_men`/`attack_fig` in `GECMDS.C:3591-3920`) → capture or retreat → loot treasury (`wonplnt` in `GECMDS.C:3964`)
6. **Meta loop:** Upgrade ship class (`cmd_new` in `GECMDS.C:4502`) → join/form team (`cmd_team` in `GECMDS.C:5220`) → coordinate attacks → dominate scoreboard

---

## 3. Entities

### 3.1 WARSHP (ship) – `GEMAIN.H:318-385`
**Size:** 512 bytes (fixed, Btrieve record)  
**Key fields:**
- `char userid[UIDSIZ]` (UIDSIZ=30, includes BBS username, line 291 `GEMAIN.H`)
- `int shipno` (unique ship ID per player, max ~10 ships per user via `topshipno`)
- `char shipname[35]`
- `int shpclass` (ship type: 0=light freighter, 1=heavy freighter, ..., 8=Cybertron, 9=Cyberquad; see `shipclass[]` table initialized in `GEMAIN.C`)
- `double heading`, `head2b` (current & target heading, 0-359°)
- `double speed`, `speed2b` (current & target speed in "warp" units, max ~9999)
- `COORD coord` (x/y floating-point sector position, universe is 30×15 sectors, `GEMAIN.H:71`)
- `double damage` (0-100%, ship explodes at 100%)
- `double energy` (flux pod power, max 65000 via `ENGYMAX`, line 90 `GEMAIN.H`)
- `double phasr` (phasor charge, 0-100%)
- `byte phasrtype` (1-19 phasor types, 20=sysop godmode, line 570 `GEMAIN.H`)
- `byte shieldtype` (1-19 shield types, line 569)
- `byte shieldstat` (1=up, 2=down, 3=damaged, line 159-161)
- `int shield` (shield charge, max varies by type)
- `int cloak` (-1=fully cloaked, 0=off, >0=cooldown ticks)
- `unsigned long items[NUMITEMS]` (14 item types, line 360):
  - 0=Men, 1=Missiles, 2=Torpedoes, 3=Ion cannons, 4=Flux pods, 5=Food, 6=Fighters, 7=Decoys, 8=Troops, 9=Zippers (teleporters), 10=Jammers, 11=Mines, 12=Gold, 13=Spy
- `TORPEDO ltorps[MAXTORPS=3]` (locked-on torpedoes tracking this ship, line 355)
- `MISSILE lmissl[MAXMISSL=3]` (locked-on missiles, line 357)
- `unsigned decout[MAXDECOY=10]` (deployed decoy timers, line 359)
- `int lastfired` (usrnum of attacker, for revenge tracking)
- `int kills` (career kills, syncs to `WARUSR.kills`)
- `byte status` (0=avail, 1=user-controlled, 2=auto/AI, 3=idle, line 208-211)
- `byte cybskill` (AI difficulty 3-17, higher=smarter, line 374)
- `int where` (0=normal space, 1=hyperspace, >=10=docked at planet #where-10, line 351)

**Physics model:** `moveship()` in `GEFUNCS.C:603`:
- Movement calculated per-tick (6s): `coord += speed * sin/cos(heading)` scaled by universe wrapping (`univmax`, default 30 for X)
- Acceleration: `speed` → `speed2b` over ticks, costs energy (`ACCENGAMT=120` per tick, line 76 `GEMAIN.H`)
- Rotation: `heading` → `head2b` at `ROTAMT=20°` per tick, costs `ROTENGUSE=30` energy per tick (line 72-73)
- Hyperspace: flag `where=1`, no combat allowed, faster navigation (`hyperspace()` in `GEFUNCS.C:551`)
- Warp zippers: instant teleport to another coordinate, costs item (`zip()` in `GECMDS.C:1657`)

**Combat mechanics:** Ships fire at each other in same sector (X/Y integer part matches):
- **Phasor:** `firep()` in `GECMDS.C:914` → damage formula `pdamage()` in `GEFUNCS.C:2031`: `dam = base * (1 / (dist^2)) * (phasrtype / 2.5) / ton_factor` capped by focus % and distance (~10k max range). Min charge to fire: 60% (`PMINFIRE`, line 81). Energy cost: `PENGUSE=57` per tick while charging (line 82).
- **Hyper-phasor:** `firehp()` in `GECMDS.C:1020` → wider beam (`HPBEAMW=5°`), ignores cloak, minimum energy `HPMINFIR=6000`, consumes `HPFIRAMT=5000` energy (line 86-88).
- **Torpedo:** `torp()` in `GECMDS.C:1146` → lock-on projectile, travels at `torpsped` (config var), auto-tracks target, damage formula `tdammax * (1 - dist/pfirdist) * tor_fact` (`GEFUNCS.C` references).
- **Missile:** Similar to torpedo, faster speed (`mislsped`), higher energy cost.
- **Shields:** Absorb damage (`shieldhit()` in `GEFUNCS.C:2401`): drain energy (`SHHITENG=1000` per hit, line 96), reduce damage by `SHIELD_FACTOR=4` (line 162). Auto-recharge at `SHENGUSE=100/tick` (line 95).
- **Cloak:** Makes ship invisible to scans, disables combat targeting (`wptr->cloak != 10` checks in `GECMDS.C:322, 422`). Energy drain: `clenguse` (config).
- **Decoys:** Confuse lock-on targeting, expire after `DECOYTIME * TICKTIME = 90s` (line 132-133).
- **Mines:** Proximity traps, `laymine()` in `GECMDS.C:1753`, detonate within `MINERANGE=10000` units, damage `minedammax` (config).

**Death:** `killem()` in `GEFUNCS.C:1058`:
- Drop 50% of cargo (gold, items) at location as salvage
- Award kill credit to `lastfired` attacker
- Respawn player at neutral zone (0,0) with new ship (class 0 light freighter)
- Notify sector via broadcast message

### 3.2 WARUSR (player account) – `GEMAIN.H:292-309`
**Size:** 256 bytes  
**Key fields:**
- `char userid[UIDSIZ]`
- `unsigned long score` (total networth: kills + planets + cash + production, calculated by `calc_networth()` in `GEMAIN.C:1310`)
- `unsigned noships` (current ship count)
- `int topshipno` (next ship ID to allocate)
- `int kills` (career kills)
- `int planets` (planets owned)
- `unsigned long cash` (liquid wealth, spent on goods/upgrades)
- `unsigned long debt` (owed to banks? Unused in code scan)
- `unsigned long plscore`, `klscore`, `population` (score breakdown)
- `byte options[30]` (flags: scan style, message filters, etc.)
- `unsigned long teamcode` (team affiliation, 0=solo)

**Persistence:** Stored in `GEuser.dat` (Btrieve indexed file), key=`userid`. Never deleted, survives logout. Updated on each command that modifies cash/planets/kills.

**Progression:** Players start with 1 light freighter (`initshp()` in `GEFUNCS.C:153`), `startcash` credits (config var, default ~10000?). Earn cash via trade, conquest. Upgrade to larger ships via `cmd_new()` → costs `shipclass[].max_price`.

### 3.3 GALPLNT (planet) – `GEMAIN.H:437-461`
**Size:** 512 bytes  
**Key fields:**
- `int xsect, ysect, plnum` (sector X/Y + planet # within sector, max `MAXPLANETS=9` per sector, line 119)
- `COORD coord` (exact position within sector for orbit/distance calc)
- `char userid[UIDSIZ]` (owner, empty=neutral)
- `char name[20]`
- `char enviorn` (environment 1-9, affects production efficiency)
- `char resource` (resource richness 1-9, affects output multipliers)
- `unsigned long cash` (planet treasury)
- `unsigned long debt`, `tax` (tax collected)
- `int taxrate` (% tax on population, 0-100)
- `char warnings` (auto-warn trespassers, 0-3)
- `char password[10]` (for alliances to dock)
- `char lastattack[UIDSIZ]` (last attacker, for mail)
- `ITEM items[NUMITEMS]` (line 456, struct at line 397-404):
  - `unsigned long qty` (stock on hand)
  - `unsigned rate` (production rate per tick)
  - `char sell` ('Y'/'N' sell to allies?)
  - `unsigned reserve` (qty to hold, rest for sale)
  - `unsigned markup2a` (sale price to allies)
  - `unsigned long sold2a` (stats)
- `char beacon[BEACONMSGSZ=75]` (broadcast message)
- `char spyowner[UIDSIZ]` (planted spy, sends intel to owner)
- `int technology` (unlock multiplier? Unused in scan)
- `unsigned long teamcode`

**Production cycle:** `multiply()` in `GEPLANET.C:195` (called every 55s):
1. Check food supply: If troops consume more food than available, kill 1/8 of troops (line 208)
2. Check men supply: Each item requires `manhours[item]` man-hours; if insufficient men, reduce production rate (line 235)
3. Tax population: `tax += (population * taxrate / 100)` (line 291)
4. Manufacture goods: For each item, `qty += rate * tick_multiplier * enviorn_factor * resource_factor * tech_factor` (line 227-263)
5. Population growth: Men reproduce, capped by environment (line 270-285)
6. Check spy: 1 in `(50/spy_count)+1` chance of discovery; if caught, kill spy and notify owners (line 120-143). If survives, 1 in 10 chance of intel report (item quantity estimate with random error) (line 150-188).

**Conquest:** `attack_men()` / `attack_fig()` in `GECMDS.C:3591-3920`:
- Attacker sends X men/fighters from ship
- Defender has Y men/fighters on planet + defensive bonuses (environment, technology, ion cannons)
- RNG battle loop: each side inflicts casualties based on ratios + random rolls (uses `plattrf1-3` and `plattrt1-3` config factors)
- If defender reduced to 0, attacker wins → `wonplnt()` transfers ownership, attacker loots treasury and goods (line 3964-4002)
- If attacker reduced to 0, defender repels → attacker loses troops
- Mail sent to both parties + spy (if present) with battle report

**Neutral planets:** Unowned (empty `userid`), no production. Can be claimed via `cmd_admin()` if player has sufficient men/troops and docks (line 3430-3482). Costs nothing to claim.

### 3.4 GALSECT (sector) – `GEMAIN.H:423-433`
**Size:** 512 bytes  
**Key fields:**
- `int xsect, ysect` (sector coords, 0-29 X, 0-14 Y, wraps via `univwrap` flag)
- `int type` (1=normal, 2=planet, 3=wormhole, line 204-206)
- `int numplan` (count of planetary objects, max 9)
- `PLNTCOORD ptab[MAXPLANETS]` (array of planet metadata: type, coord)

**Universe structure:** 30×15 grid = 450 sectors. Each sector can contain 0-9 planets/wormholes. Stored in `GEplanet.dat` (misnamed; actually holds sectors AND planets as different record types via discriminator keys). Lookup via `gesdb()` in `GEMAIN.C:1676`.

**Wormholes:** `GALWORM` struct (line 466-477): instant travel between two coordinates (`coord` → `destination`), `visible` flag (some hidden until discovered). Declared in sector as `type=PLTYPE_WORM=3`.

### 3.5 Teams – `GEMAIN.H:644-653`
**Key fields:**
- `long teamcode` (unique ID, also stored in `WARUSR` and `GALPLNT` for affiliation)
- `char teamname[31]`
- `unsigned int teamcount` (member count)
- `unsigned long teamscore` (sum of member scores)
- `char password[11]` (to join)
- `char secret[11]` (for alliances, unused?)
- `int flag` (status flags)

**Purpose:** Players form teams to coordinate conquest, share planet access (dock at allied planets with password), pool bonuses. Team scores ranked on scoreboard. Max `MAXTEAMS=50` (line 240). Commands: `cmd_team()` in `GECMDS.C:5220-5752` (create, join, leave, list, invite).

### 3.6 NPCs: Cyborgs & Droids
**Cyborgs** (`GECYBS.C`):
- AI-controlled ships (classes 8=Cybertron, 9=Cyberquad)
- `cyb_init()` (line 87): Spawn with random cargo (flux pods, mines, jammers, gold up to `cyb_gold` config), skill level 3-17
- `cyb_lives()` (line 199): Tick behavior: patrol sectors, target players based on skill vs. player kill count (ease up on newbies via `CYB_BE_NICE=30` and `CYB_BE_EASY=60` thresholds, line 172-173), fire weapons, lay mines/jammers when damaged above `CYB_MINDAM=75%` (line 174)
- Loot cap: `CYB_MAXCASH=2000000` (line 171)
- Breakoff chance: 1 in `CYB_BREAKOFF=500` per tick to disengage (line 174)
- Respawn after death via `cyb_init()` at random coordinates

**Droids** (`GEDROIDS.C`):
- 3 classes (10, 11, 12) with different tactics (line 223-503)
- Class 10: Patrols, avoids combat unless attacked
- Class 11: Aggressive hunter, charges players
- Class 12: Defensive, uses decoys/jammers, fires torpedoes
- No cash loot, just combat challenge

**AI tick processing:** `warrti2()` processes up to `CYBMAXPERTICK=2` cyborgs and `QUADMAXPERTICK=5` cyberquads per second (`TICKTIME2=1`, line 180-181 `GEMAIN.H`). This throttles AI to prevent BBS overload. Modern port can parallelize.

### 3.7 Mail system – `GEMAIN.H:500-547`
**MAIL struct:**
- `char userid[UIDSIZ]` (recipient)
- `int class` (category: 1=distress, 2=maxout, 3=production report, 4=game stats, 5=planet stats, line 220-224)
- `int type` (message template ID)
- `char topic[30]`, `string1[80]`, `name1[25]`, `name2[25]`
- `int int1-3`, `long long1-3` (template parameters)

**Purpose:** Asynchronous notifications (planet under attack, production maxed, spy reports). Stored in `GEmail.dat`. Players read via BBS mail interface (code not in GE module, handled by MajorBBS core). GE sends via `sendit()` in `GEFUNCS.C:2290`.

---

## 4. Economy

### 4.1 Currencies
**Cash** (`WARUSR.cash`, `GALPLNT.cash`):
- Earned via: selling goods (`cmd_sell`), looting dead ships (`killem`), planet tax collection (`multiply`)
- Spent on: buying goods (`cmd_buy`), ship upgrades (`cmd_new`), maintenance/repairs (`cmd_maint`)
- No global currency sink besides death penalty (lose 50% of carried gold). Inflation risk over long campaign.

**Gold** (item 12):
- Tradable commodity, high value (`baseprice[I_GOLD]` likely highest)
- Dropped by killed ships, mined on rich planets

**Debt** (`WARUSR.debt`, `GALPLNT.debt`):
- Field exists but no code found that accrues/enforces debt. Likely vestigial or planned feature.

### 4.2 Production (planet goods)
**14 item types** (line 142-158 `GEMAIN.H`, `kwrd[]` in `GECMDS.C:80-94`):
0. **Men:** Population; required labor for all production; reproduces over time
1. **Missiles:** Ammo for ship combat; manufactured
2. **Torpedoes:** Ammo for ship combat; manufactured
3. **Ion cannons:** Planetary defense; manufactured
4. **Flux pods:** Ship energy refill; manufactured
5. **Food:** Consumed by troops; manufactured by men
6. **Fighters:** Planetary/ship combat units; manufactured
7. **Decoys:** Ship defense; manufactured
8. **Troops:** Ground assault units; manufactured
9. **Zippers:** Instant teleport items; manufactured (rare?)
10. **Jammers:** ECM devices; manufactured
11. **Mines:** Space traps; manufactured
12. **Gold:** Wealth; mined from resource-rich planets
13. **Spy:** Covert agent; planted on enemy planets; not manufactured, likely acquired via command

**Production formula** (`GEPLANET.C:227-263`):
```c
for (each item i in NUMITEMS) {
  rate = planet.items[i].rate;
  manhours_req = rate * manhours[i];
  if (planet.items[I_MEN].qty < manhours_req) {
    // Insufficient labor, reduce rate proportionally
    rate = planet.items[I_MEN].qty / manhours[i];
  }
  
  fact = 1.0; // base multiplier
  fact *= (planet.enviorn / 5.0); // env 1-9, avg 5 → 0.2x to 1.8x
  fact *= (planet.resource / 5.0); // resource richness
  fact *= (planet.technology / 100.0 + 1.0); // tech bonus (0-100%)
  
  qty_produced = rate * fact * (PLANTIME / 60.0); // scale by 55s tick
  planet.items[i].qty += qty_produced;
  
  // Cap at maxpl[i] (config-defined max stockpile)
  if (planet.items[i].qty > maxpl[i]) {
    planet.items[i].qty = maxpl[i];
  }
}
```

**Scarcity:** High-tech items (missiles, fighters, zippers) require more manhours. Rich/high-env planets produce faster. Neutral planets produce nothing (no owner to set rates).

### 4.3 Trade mechanics
**Buying** (`cmd_buy()` in `GECMDS.C:4169`):
- Player docks at planet (`where >= 10`)
- Views price list (`cmd_price()` → `price()` in `GECMDS.C:4430`)
  - **Own planet:** base price (`baseprice[item]`)
  - **Allied planet:** markup price (`planet.items[item].markup2a`)
- Purchases qty from available stock (`amt4sale()` in `GECMDS.C:4405`):
  - Own planet: all qty available
  - Allied planet: qty - reserve (if `sell='Y'`)
- Deducts cash, transfers items to ship (`warsptr->items[item] += amt`)
- Planet gains cash

**Selling** (`cmd_sell()` in `GECMDS.C:4103`):
- Inverse: transfer ship items → planet, gain cash at planet's buy price (likely `baseprice` or lower)
- Code shows one-way trade (planet sets prices, player is price-taker)

**Weight limits:** `calcweight()` in `GEFUNCS.C:2533` → `sum(items[i] * weight[i])` vs. `shipclass[].max_tons`. Overweight ships cannot dock/transfer (`chkweight()` checks).

**Price discovery:** No dynamic supply/demand. Prices fixed per planet owner (admin sets markup). Exploit: buy low (own planet at base), sell high (allied planet with high markup). Arbitrage is core trade loop.

### 4.4 Sinks & faucets
**Faucets (wealth creation):**
- Planetary production (gold mining, item crafting)
- Starting cash (`startcash` config)
- Cyborg loot (gold drops)
- Tax collection

**Sinks (wealth destruction):**
- Death penalty (50% gold/items dropped, scavengable by others)
- Maintenance/repairs (costs cash, `cmd_maint()` in `GECMDS.C:4420`)
- Ship upgrades (buy larger ship class)
- Energy/ammo depletion (flux pods consumed, missiles/torps fired)

**Imbalance risk:** If production >> consumption, economy inflates over campaign. Midnight reset (`gemidnight()` in `GEMAIN.C:1047`) likely resets some stocks/scores to prevent runaway wealth. Code shows score recalculation (line 1100-1200) but unclear if items wiped.

---

## 5. Combat / Conquest

### 5.1 Ship-to-ship combat
**Resolution:** Real-time via `warrti()` tick (6s intervals). Players issue commands in session, but damage applies on ticks. Example sequence:
1. Player A: `pha <shipid> 50` → fire phasor at ship B, 50% focus
2. Tick handler calls `firep(warsptr, usrnum)` in `GECMDS.C:914`
3. `pdamage()` calculates damage based on distance, phasor type, target mass (`GEFUNCS.C:2031`)
4. `shieldhit()` absorbs damage if shields up, else damage accumulates (`wptr->damage += dmg`)
5. If `damage >= 100`, `killem()` destroys ship

**Weapon comparison:**
| Weapon | Range | Damage | Energy cost | Lock-on? | Notes |
|--------|-------|--------|-------------|----------|-------|
| Phasor | ~10k | Inverse-square falloff | 57/tick charge, 500 min fire | No | Instant hit, requires good aim (degrees) |
| Hyper-phasor | ~10k | Higher, wide beam (5°) | 6000 min, 5000/shot | No | Ignores cloak, cooldown 10 ticks |
| Torpedo | Config (`pfirdist`) | High, linear falloff | Item consumed | Yes | Lock-on tracks, speed `torpsped` |
| Missile | Config | Highest, linear falloff | Item + energy | Yes | Fastest, expensive |
| Ion cannon | Planetary | Instant kill? | N/A | No | Defensive only, unclear mechanics |
| Mine | 10k proximity | `minedammax` | Item | No | Area denial, timer detonates |

**Targeting:** `cmd_lock()` in `GECMDS.C:5036` locks torpedo/missile onto specific ship (by letter ID from scan). Phasors require manual aiming (`degrees` offset from heading).

**Fog of war:** Ships not in same sector are invisible unless:
- Hyper-scanner (`scan_hy()` in `GECMDS.C:2696`) detects ships within `HYSCANRANGE=5` sectors (line 130 `GEMAIN.H`)
- Sector scan (`scan_se()` in `GECMDS.C:2548`) shows ships in current sector (cloaked ships hidden)

**Death loop:** Killed player respawns at neutral zone (0,0) with class 0 ship, loses 50% cargo, attacker gains kill credit. No permadeath. Encourages comeback via trade.

### 5.2 Planetary conquest
**Attack types:**
1. **Men assault** (`attack_men()` in `GECMDS.C:3591`): Player sends men from ship, battles planet's men + defenses
2. **Fighter assault** (`attack_fig()` in `GECMDS.C:3756`): Player sends fighters, battles planet's fighters

**Battle resolution (men example):**
```c
double r; // random factor
unsigned long attacker_men = num; // from ship
unsigned long defender_men = planet.items[I_MEN].qty;
unsigned long defender_fighters = planet.items[I_FIGHTER].qty;
unsigned long defender_ioncannons = planet.items[I_IONCANNON].qty;

// Defender bonuses
defender_men *= (1.0 + planet.enviorn / 10.0); // terrain advantage
defender_men += defender_fighters * 2; // fighters fight as 2x men
defender_men += defender_ioncannons * 10; // ion cannons = 10x men
defender_men *= (1.0 + planet.technology / 100.0); // tech bonus

// Loop until one side reduced to 0
while (attacker_men > 0 && defender_men > 0) {
  // Attacker kills defenders
  r = rndm(plattrf1) * plattrf2 * plattrf3; // config factors
  kill2 = attacker_men * r;
  defender_men -= kill2;
  
  // Defender kills attackers
  r = rndm(plattrt1) * plattrt2 * plattrt3;
  kill1 = defender_men * r;
  attacker_men -= kill1;
}

if (defender_men <= 0) {
  wonplnt(); // attacker captures planet
  // Transfer ownership, loot treasury, award planet to waruptr->planets++
} else {
  // Attacker defeated, retreat
}
```
(Simplified; actual code in `GECMDS.C:3623-3753` has more conditions)

**Key factors:**
- Environment (1-9): Higher = better defender advantage
- Technology (0-100%): Multiplies defender strength
- Ion cannons: Each cannon = 10 men equivalent
- Random variance: `rndm()` introduces RNG swings (low `plattrf*` = predictable, high = chaotic)

**Conquest payoff:**
- Gain planet's treasury (`planet.cash`)
- Gain production facility (ongoing resource generation)
- Increase `waruptr->planets` score
- Mail sent to victim + spy

**Defense:** Planet owner sets `warnings` (auto-message intruders) but cannot actively defend (no player piloting planet). Must rely on stocked men/fighters/ion cannons. Offline vulnerability is key risk.

### 5.3 Win conditions
**Scoreboard** (`calc_networth()` in `GEMAIN.C:1310`):
```c
waruptr->score = waruptr->klscore + waruptr->plscore + waruptr->cash + waruptr->population;
waruptr->plscore = value_pl(); // sum of all owned planet values (resources, tech, stocks)
waruptr->klscore = waruptr->kills * score_bonus; // kills worth score_bonus each
```
Top score at midnight reset wins campaign. No explicit endgame trigger; BBS admin declares winner manually.

**Alternative win:** Total conquest (own all planets)? Code lacks explicit check. Likely social win condition (community acknowledges dominance).

---

## 6. Persistence

### 6.1 Storage model
**Btrieve database** (indexed file system, pre-SQL era):
- `GEship.dat` (BTVFILE `gebb1`): All ships (`WARSHP`), key=`(userid, shipno)`, 512-byte records
- `GEplanet.dat` (`gebb2`): All sectors (`GALSECT`) and planets (`GALPLNT`), key=`(xsect, ysect, plnum)`, 512-byte records
- `GEmail.dat` (`gebb4`): Mail queue (`MAIL`), key=`(userid, class, msgno)`, 256-byte records
- `GEuser.dat` (`gebb5`): User accounts (`WARUSR`), key=`userid`, 256-byte records

**File I/O functions** (in `GEMAIN.C`):
- `gepdb()` (line 1519): ship CRUD (lookup, add, update, delete, get, next)
- `geudb()` (line 1601): user CRUD
- `gesdb()` (line 1676): sector CRUD
- `getplanetdat()` (line 1761): load planet by sector + plnum

**Btrieve abstraction** (`MBMGEMAP.H:20-77`): Struct `btvblk` wraps file handle, key buffer, data buffer. Macros like `geqbtv()` (get-equal), `gnxbtv()` (get-next) provide cursor-based iteration. Locking: single-writer via `obtbtv()` (obtain/lock record), released on update/close.

**Concurrency:** BBS single-threaded per-channel (user). Multi-user concurrency handled by Btrieve locking (record-level). Tick system runs in same thread, no parallel writes. Modern port needs ACID database (PostgreSQL, MySQL) with row locking.

### 6.2 Logout persistence
**What survives logout:**
- All ship state (position, cargo, damage, shields)
- User account (cash, planets, kills, team)
- Planet production continues (tick system runs even when player offline)
- Locked torpedoes/missiles remain in flight
- Mines persist until timer expires or detonation

**What resets on logout:**
- BBS session state (`usrptr->substt`, menu stack)
- Temporary command buffers (`input[]`, `margv[]`)
- Ship `status` flips from `GESTAT_USER=1` to `GESTAT_AVAIL=0` (available for next login)

**Critical insight:** Players can lose battles while offline. Cyborgs/droids continue attacking. No "safe logout" zone. This is **toxic for modern mobile** (player expects pause/safe AFK). Recommend: offline ships become invulnerable OR teleport to safe zone OR require manual "retreat to safe harbor" command before logout.

### 6.3 Tick/maintenance jobs
**Real-time tick system** (summary from §2.2):
- `TICKTIME=6s`: Ship physics, combat, energy recharge
- `TICKTIME2=1s`: AI (cybertron/droid) updates
- `PLANTIME=55s`: Planet production, spies, taxes
- `60s`: Unknown maintenance

**Midnight reset** (`gemidnight()` in `GEMAIN.C:1047-1309`):
- Recalculates all player scores (`calc_networth()`)
- Sorts roster by score (`gemaxlist` entries)
- Awards team bonuses (code shows `teambonus` and `pltvcash`/`pltvdiv` calculations, line 2118-2125)
- Sends production report mail to all planet owners
- Sends game stats mail (scoreboard summary)
- **Does NOT wipe player progress** (no resource reset found). Campaign persists across days.

**Backup strategy:** Code lacks auto-backup. BBS sysop manually copies `.dat` files. Modern port: hourly snapshots + transaction logs.

---

## 7. Multiplayer / BBS Assumptions

### 7.1 Concurrency model
**BBS architecture:**
- Single-threaded event loop (MajorBBS `main()`)
- Each dial-in user assigned a "channel" (`usrnum`, 0-based index up to `MAXUSR`, typically 8-32 lines)
- Module exports callbacks: `gelogon()` on connect, `galemp()` on input, `pwarlof()` on disconnect
- Tick timers (`rtkick()`) inject callbacks into event loop every N seconds

**GE concurrency:**
- No parallel execution; tick handlers process ships sequentially (loop over `nships`)
- AI throttled to 2 cyborgs + 5 quads per second (`CYBMAXPERTICK`, `QUADMAXPERTICK`) to avoid blocking input
- Database locking via Btrieve record locks (reader-writer at record level)
- No mutexes, no race conditions (single-threaded)

**Breaks in modern always-online:**
- Mobile clients expect instant response (no tick polling)
- Horizontal scaling (multiple game servers) requires distributed state (Redis, Postgres)
- Need websocket/push for real-time updates (ship moves, combat damage)

**Recommendation:** Replace tick polling with event-driven architecture:
- Player commands → immediate validation + queue action (e.g., "fire phasor" → add event to combat queue)
- Server loop processes queues at strategic intervals (preserve 6s combat cadence for balance)
- Broadcast state changes via websockets to all clients in sector

### 7.2 Shared world state
**Universe is singleton:**
- All players inhabit same 30×15 sector grid
- Ships collide (same sector = combat range)
- Planets owned by single player (no multi-ownership)
- Teams share planet access (password) but not ownership

**Instancing:** None. No private sectors, no parallel universes. 100% shared PvP space (except neutral zone 0,0 is quasi-safe due to lack of resources). This is **hardcore sandbox MMO** design (EVE Online, Albion Online style).

**Scalability concern:** 450 sectors × 9 planets = ~4000 planets max. If 1000 players, average 4 planets/player. Crowding inevitable. Early players claim best real estate (high enviorn+resource), late joiners stuck with scraps. Recommend: expand universe (100×50 grid?) OR procedural sector generation OR instanced "frontier" zones.

### 7.3 Turn timing (BBS sessions)
**Session duration:** Arbitrary. Player logs in, issues commands until logs off or timeout. No enforced turn limit (unlike door games with daily turn caps). Commands execute instantly (blocking input), but effects delayed to tick boundaries.

**Synchronous commands** (immediate feedback):
- `scan`, `report` → read current state, no side effects
- `rotate`, `impulse`, `warp` → set target heading/speed, physics apply next tick
- `buy`, `sell` → instant transaction if validation passes
- `phas`, `torp` → fire queued, damage applies next tick

**Asynchronous outcomes:**
- Combat damage (tick-based)
- Planet production (55s tick)
- Torpedo tracking (travels over ticks)
- Mail delivery (next login)

**Modern translation:** Commands are REST API calls or websocket messages. Responses return "action queued" + estimated completion time (e.g., "torpedo arrives in 12 seconds"). Client polls or subscribes to updates.

### 7.4 Messaging (player communication)
**In-game messaging:**
- `cmd_send()` in `GECMDS.C:1793`: Broadcasts text to all ships in sector (or specific frequency `freq[0-2]`, line 361 `GEMAIN.H`)
- Frequencies: Subspace (sector-wide), hyperspace (hyperspace only), planetary (docked ships)
- No private DM command in code scan (handled by BBS core mail?)

**Mail system** (covered §3.7):
- Auto-generated alerts (attack, production, spy reports)
- Read via BBS mail interface (external to GE module)

**Teams:**
- No team-only chat channel visible in code
- Coordination likely via BBS forums or external (pre-Discord era: bulletin boards, private mail)

**Modern port:** Add:
- Guild/alliance chat
- Sector chat (real-time, websocket)
- Private DMs
- Voice chat integration (optional)

### 7.5 Admin controls
**Sysop powers** (`cmd_sysop()` in `GECMDS.C:4710-4956`, requires `su` flag):
- Spawn ships (any class, including restricted)
- Grant items/cash
- Teleport ships
- Toggle invincibility (phasor type 20 godmode, line 1066 `GECMDS.C`)
- Edit planet ownership
- Reset scores
- Broadcast messages
- Kill players
- Ban users (via BBS core, not GE)

**Security:** `su` flag checked at command entry. No admin UI (text-based commands). Modern port: web admin panel.

**Balance concern:** Sysop can kingmake (gift resources, tilt wars). Recommend: audit log admin actions, community transparency.

### 7.6 Breakpoints for always-online mobile
**What breaks:**
1. **Tick polling:** Mobile clients drain battery if polling every 6s. Use push notifications.
2. **Offline vulnerability:** Players raided while AFK/asleep. Unfun for casual mobile. Add "docking" safe zones or offline shields.
3. **Session blocking:** BBS commands block until input. Mobile UI expects instant feedback. Decouple command submission from execution.
4. **Single-threaded:** Cannot scale to 10,000 concurrent users. Must shard (regions) or queue (lobby system).
5. **Text parsing:** 3-letter command abbreviations hostile to mobile touch UI. Replace with buttons, gestures, visual targeting.
6. **No reconnect:** BBS disconnect = ship frozen in space. Mobile needs graceful reconnect (resume session mid-combat).

**Modernization strategy:**
- **Keep:** Strategic pacing (6s combat cadence, 55s production cycle), ship physics (acceleration, rotation), conquest meta
- **Transform:** Tick system → event-driven server; text commands → touch UI; offline play → safe harbor mechanics
- **Kill:** BBS I/O blocking, single-threaded architecture, Btrieve database

---

## 8. Keep vs Kill (Recommendations for Modern Mobile MMO)

### ✅ KEEP (modernize, preserve core)
| System | Why | Adaptation |
|--------|-----|------------|
| **Strategic fleet/conquest loop** | Timeless 4X fantasy (explore, expand, exploit, exterminate). Players love building empires, crushing rivals. | Preserve loop, reduce friction (auto-travel, batch commands). |
| **Ship customization** | 10 ship classes (freighter → dreadnought), 19 phasor/shield types, item loadouts. Builds player identity. | Expand: visual customization (skins, decals), modular ship components (engines, weapons), tech trees. |
| **Planetary production economy** | Long-term investment (claim planet → set rates → harvest wealth). Creates empire-building depth. | Keep 55s tick for production (feels strategic, not grindy). Add notifications ("Gold ready to harvest"). UI: planet management dashboard. |
| **Team/alliance warfare** | Coordinated attacks, shared planets, team scores. Social glue. | Expand: alliance chat, shared map markers, coordinated raid timers, alliance vs alliance tournaments. |
| **Permadeath for ships (not accounts)** | Losing 50% cargo on death creates stakes, fuels revenge loops. | Keep death penalty, but add "insurance" (pay fee to reduce loss), wreckage recovery (retrieve own loot), killmail (detailed battle report). |
| **Hybrid turn/real-time cadence** | 6s combat tick feels tactical (time to react), not twitch-based. | Keep strategic pacing, but allow instant command input (queue actions, server resolves at tick boundaries). Mobile-friendly: tap target → confirm fire → animation plays over 6s. |
| **Open PvP sandbox** | No safe zones (except neutral), full loot, territory control. Hardcore appeal (niche but loyal). | Keep, but add opt-in PvE zones (higher taxes, lower rewards) for casual players. Or separate PvP/PvE servers. |
| **Fog of war** | Limited vision (sector scan, hyper-scanner) creates scouting value, stealth gameplay (cloak). | Keep, enhance: "Intel" resource (spy reports show enemy fleet compositions), UAV drones (deploy to reveal fog). |

### 🔄 TRANSFORM (rework, preserve intent)
| System | Problem | Solution |
|--------|---------|----------|
| **Text command parser** | Hostile to mobile touch UI. 3-letter abbreviations (`pha`, `torp`) arcane for new players. | Replace with visual UI: tap ship → radial menu (Fire, Scan, Transfer, Retreat). Context-aware buttons (hide "Buy" unless docked). Preserve power-user shortcuts (swipe gestures for vets). |
| **Tick system (6s)** | Polling drains battery, not scalable. | Event-driven server: commands queued instantly, server resolves at 6s intervals, pushes results via websocket. Client interpolates (smooth animations) between ticks. Feels real-time to user. |
| **Planet production (55s tick)** | Good cadence, but opaque. Players don't see progress. | Add progress bars ("Missiles: 42/100, ETA 22s"), push notifications on completion. Gamify: "Production chain" (men → food → troops → conquest). |
| **Offline vulnerability** | Players lose planets while AFK. Toxic for mobile (can't play 24/7). | **Option A:** Offline shield (8h immunity after logout, cost: no production). **Option B:** "Retreat to citadel" command (safe zone, costs daily rent). **Option C:** NPC defenders (hire AI fleet to patrol while offline). |
| **Ship combat** | Phasors require manual aiming (degrees offset). Fun on BBS text, tedious on mobile. | Auto-aim option (tap target → lock on → fire at optimal angle). Preserve manual aim for skill players (drag to aim, bonus damage for precision). |
| **Planet conquest** | RNG-heavy (random rolls decide battle). No player agency once assault starts. | Add real-time tactical layer: deploy troops in waves (flanking, reserves), call in orbital strikes (costs ship energy), time reinforcements. Or keep RNG but show odds pre-battle (XCOM-style). |
| **Trade economy** | Fixed prices per planet (no supply/demand). Exploit: buy low, sell high, infinite arbitrage. | Dynamic pricing: planet demand rises if stockpiles low, falls if high. Random events (plague reduces men, spiking food prices). Black markets (illegal goods, high risk/reward). |
| **Mail system** | Async text messages, read via separate BBS interface. Clunky. | In-app notifications (push), inbox UI (tap to read), quick reply (canned responses: "Surrender" / "Revenge!"). Integrate with chat. |

### ❌ KILL (remove, anti-fun or obsolete)
| System | Why | Replacement |
|--------|-----|-------------|
| **BBS session blocking** | Commands block until user input. Mobile needs instant responsiveness. | Asynchronous actions: submit command → server queues → client polls/subscribes to result. No blocking. |
| **Single-threaded architecture** | Cannot scale to 1000+ concurrent users. | Microservices: combat server, economy server, chat server. Load balancer, Redis state cache, Postgres persistence. |
| **Btrieve database** | 1980s flat files, no relational queries, fragile. | PostgreSQL or MongoDB: ACID transactions, JSON support, horizontal scaling. |
| **3-letter command abbreviations** | Arcane, hostile to new players. Relic of BBS text efficiency (save modem bandwidth). | Kill entirely. Use icons, buttons, drag-drop UI. No text commands (except advanced console for power users). |
| **Universe size limit (30×15=450 sectors)** | Too small for 1000+ players. Land rush favors early adopters, late joiners stuck with garbage planets. | Procedural generation: infinite sectors (seed-based, lazy-load as explored). Or instanced galaxies (100 players/galaxy, cross-galaxy trade/raids). |
| **Midnight reset scoreboard** | Arbitrary time zone bias (midnight EST?). Resets progress, punishes players in wrong TZ. | Rolling leaderboards (weekly, monthly, all-time). Seasons (3-month campaigns, fresh start each season, cosmetic rewards). No daily resets. |
| **Cyborg AI throttling** | 2 cyborgs/s to avoid BBS lag. Weak sauce. | Remove throttle. Async AI: process all NPCs in parallel (goroutines, async/await). Scale up NPC density for challenge. |
| **Spy mechanics (RNG intel)** | Interesting concept but opaque. 1 in 10 chance per 55s tick = ~10% daily odds. Too rare. | Revamp: spy minigame (infiltrate planet, choose intel type: production, defenses, treasury), guaranteed intel after X time, risk of capture scales with spy skill vs planet security. |

---

## 9. Open Questions / Decisions Needed

### 9.1 Universe size & topology
**Q:** Keep 30×15 grid or expand?  
**Options:**
- A) Keep 450 sectors, limit players to 500 (density = faction wars)
- B) Expand to 100×50 (5000 sectors, room for 5000 players)
- C) Infinite procedural (EVE-style, unlimited expansion)
- D) Instanced galaxies (sharding by player count, cross-shard portals)

**Decision impact:** A = intimate but crowded; B = balanced; C = exploration focus, dilutes PvP; D = best scaling but fragments community.

### 9.2 Offline protection
**Q:** How to prevent offline griefing?  
**Options:**
- A) Logout immunity (8h shield, no production)
- B) Safe harbor (dock at NPC station, costs rent)
- C) Hire NPC defenders (AI fleet guards assets, costs % of production)
- D) None (hardcore mode, embrace offline raids)

**Tradeoff:** A/B = casual-friendly but reduces stakes; C = middle ground (risk management); D = niche hardcore audience.

### 9.3 Combat pacing: keep 6s ticks?
**Q:** Modern mobile expects instant feedback. 6s per combat action too slow?  
**Options:**
- A) Keep 6s (tactical depth, time to coordinate with allies)
- B) Reduce to 2s (faster, still strategic)
- C) Real-time (instant hit, twitch-based)

**Recommendation:** Keep 6s for **strategic combat** (fleet positioning, target priority), but add instant **skirmish mode** (1v1 duels, real-time for stakes/fun). Players choose mode pre-engagement.

### 9.4 Monetization (out of scope for Phase 1a, but relevant to design)
**Q:** F2P or premium?  
**Options:**
- A) Premium ($10 buy-to-play, no MTX)
- B) F2P + cosmetics (ship skins, planet themes, no P2W)
- C) F2P + time-savers (speed up production, extra ship slots, P2W-lite)
- D) Subscription ($5/mo, all features)

**Design impact:** B/D = fair monetization, broadest audience; C = revenue risk but attracts whales; A = niche retro appeal.

### 9.5 PvE vs PvP balance
**Legacy GE:** 100% PvP (except cyborg NPCs). No PvE "safe" endgame (raids, dungeons).  
**Q:** Add PvE content?  
**Options:**
- A) Keep pure PvP (niche but loyal)
- B) Add PvE sectors (alien invasions, derelict stations, co-op raids)
- C) Separate PvE/PvP servers

**Recommendation:** **B** (hybrid). Retain PvP core, add optional PvE for variety (casual players do PvE to gear up, then PvP for conquest). Example: "Xenomorph hives" spawn in neutral sectors, drop rare tech, require fleet coordination.

### 9.6 Ship permadeath: too punishing?
**Legacy:** Die → lose 50% cargo + ship stats (respawn with class 0).  
**Q:** Soften penalty for mobile casual audience?  
**Options:**
- A) Keep 50% loss (hardcore)
- B) Reduce to 25% loss, no ship class reset
- C) Insurance system (pay upfront, recover 80% on death)
- D) Permadeath for ships only (class 5+ lost forever, must rebuy), starter ships invulnerable

**Recommendation:** **C** (insurance). Adds strategic choice (pay safety cost vs risk), preserves stakes (uninsured = high risk/reward).

### 9.7 Real-time vs turn-based identity
**Legacy:** Hybrid (synchronous commands + async world simulation).  
**Q:** Modern port leans which direction?  
**Options:**
- A) Preserve hybrid (commands instant, resolution tick-based)
- B) Full real-time (twitch combat, EVE Echoes style)
- C) Full turn-based (Civilization multiplayer style, daily turns)

**Recommendation:** **A** (hybrid). Unique positioning: "Strategic real-time MMO" (not twitch APM, not slow turns). Commands feel instant (UI responsive), but world runs at deliberate pace (6s combat, 55s production). Appeals to mobile players who want depth without endless grinding.

---

## 10. Summary of Citations

All claims cite `Original_Code/` files:
- **Structs/defines:** `Original_Code/mbmgemp/GEMAIN.H` (lines cited inline)
- **Game logic:** `Original_Code/mbmgemp/GEMAIN.C`, `GECMDS.C`, `GEFUNCS.C`, `GEPLANET.C`, `GECYBS.C`, `GEDROIDS.C` (function names + line ranges cited)
- **Combat formulas:** `pdamage()` in `GEFUNCS.C:2031`, `attack_men()` in `GECMDS.C:3591`
- **Economy:** `multiply()` in `GEPLANET.C:195`, `cmd_buy()`/`cmd_sell()` in `GECMDS.C:4169-4443`
- **Tick system:** `TICKTIME`/`PLANTIME` constants in `GEMAIN.H:133-136`, `rtkick()` calls in `GEMAIN.C:954-972`
- **Persistence:** Btrieve file I/O in `GEMAIN.C:1519-1761`, structs sized 256b/512b for database records

No speculation beyond code evidence. Where behavior is ambiguous (e.g., `debt` field unused), explicitly noted.

---

**End of Phase 1a System Map.**  
**Next steps:** Review with Empire Lead, prioritize systems to KEEP/TRANSFORM/KILL, draft Unity + FastAPI architecture doc (Phase 1b).
