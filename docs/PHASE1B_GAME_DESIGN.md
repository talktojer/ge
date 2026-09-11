# Phase 1b: Game Design – Galactic Empire Mobile MMO

**Date:** 2026-09-11  
**Phase:** Design-only (no implementation)  
**Source of truth:** `docs/PHASE1A_LEGACY_SYSTEM_MAP.md` (PR #1)  
**Target platform:** iOS + Android (Unity Editor 6000.4.10f1 + FastAPI backend)

---

## 1. Executive Summary

**Player fantasy:** Command a space fleet, conquer a living galaxy, build an empire that matters—all from your phone.

**One-sentence pitch:** Galactic Empire is a strategic mobile MMO that delivers EVE Online's territorial conquest and persistent economy in 2–5 minute sessions, where every command you issue ripples across a shared universe while you're away.

**Phase 1b scope:** This document establishes the game design foundation for the modern mobile reimagining of MajorBBS Galactic Empire. It translates the legacy BBS space-conquest fantasy into a mobile-first live MMO with glanceable territory management, asynchronous strategic pacing, and persistent faction warfare. **No implementation code is included**—only design decisions, systems architecture, player loops, and handoff requirements for Client UX and Stack teams.

**Core design pillars:**
1. **Strategic fleet combat** (not twitch): ~6-second combat resolution preserves tactical depth over APM
2. **Persistent shared galaxy**: All players inhabit sharded universe instances; your empire grows/defends 24/7
3. **Async-friendly sessions**: 2-minute commands that move a long game (issue orders → close app → return to consequences)
4. **Mobile-optimized identity**: No BBS menus, no 3-letter text commands—tap, swipe, conquer

**Transformation thesis:** Keep the space-conquest meta (explore/claim/produce/conquer) that made legacy GE timeless. Kill the BBS I/O constraints (text parser, tick polling, offline vulnerability). Transform the pacing from session-blocking turns to instant-command/deliberate-resolution hybrid that respects mobile battery, attention, and always-online expectations.

---

## 2. Player Fantasy

### 2.1 Who Is The Player?

You are an **empire admiral** commanding a fleet in a living, player-driven galaxy. Not a solo hero grinding story missions—a strategic peer in a persistent war economy where your decisions (claim this planet, ally with that faction, strike at dawn) have consequences that unfold over hours and days.

**Core fantasy beats:**
- **Morning:** Check your phone. Overnight, your mining colonies produced 10k gold. Your alliance took three enemy sectors. You're under attack—enemy fleet inbound in 90 seconds. Issue defend order, close app, grab coffee.
- **Lunch break:** 5 minutes. Scout a new frontier sector, claim an undefended high-resource planet, set production rates (fighters > gold > food), deploy defensive fleet. Done.
- **Evening:** 20 minutes. Coordinate with alliance for a synchronized strike on rival faction's industrial hub. Jump into the sector, launch torpedoes, loot the wreckage, split the take. Victory notification pings all day as alliance members cash in.
- **Weekend:** 2-hour war. Your faction's 48-hour territorial campaign climaxes. Fleet positioning, feints, backstabs, trash talk in alliance chat. The galaxy map shifts. Leaderboards crown winners. Season rewards drop.

### 2.2 What "Empire" Means On A Phone

**Not this:** Sitting at a desktop for 6-hour sessions manually piloting every ship (EVE Online PC).  
**Not this:** Daily turn submission like Civilization asynchronous MP (too slow for mobile cadence).

**This:**
- **Glanceable territory:** Map shows your 12 planets at a glance—green (safe), yellow (under threat), red (under attack). Tap to inspect, swipe to issue orders.
- **Async power:** Your fleets patrol, your planets produce, your alliances defend—all while you're offline. You set strategic directives; the world executes them.
- **Short commands, long consequences:** 30 seconds to issue "Attack sector (50,30) with Fleet Alpha at 14:00 UTC" → close app → return hours later to loot and casualties.
- **Mobile-first identity:** Voice of push notifications ("Colony #7 Gold Reserves Full"), haptic feedback on torpedo hits, portrait-mode empire dashboard, landscape-mode tactical combat view.

**Empire builder, not micromanager.** You don't babysit every trade route; you set tariffs and watch cash flow. You don't manually fire every shot; you position fleets and declare rules of engagement (aggressive, defensive, flee if outnumbered). The game respects your time while delivering the dopamine of conquest.

---

## 3. Core Loops

### 3.1 Legacy → Modern Mapping

Phase 1a identified six legacy loops (§2.3). Here's how they modernize for mobile:

| Legacy Loop | Modern Translation | Session Fit |
|-------------|-------------------|-------------|
| **Exploration** | Swipe galaxy map, tap unexplored sector, auto-pilot fleet to investigate, receive push notification on arrival ("Sector 127: 3 planets detected"). | 2 min (queue travel) + async wait |
| **Trade** | Set trade routes (Planet A excess food → Planet B deficit food), AI convoys auto-execute, collect profit notifications. Manual trade for rare goods (salvage, alien tech). | 3 min (route setup), passive income |
| **Colony** | Tap unclaimed planet → "Claim" button → set production sliders (Men 40%, Fighters 30%, Gold 30%), confirm. Planet produces every 55 seconds; notification when stockpiles hit cap. | 2 min (claim + configure) |
| **Ship combat** | Tap enemy fleet → radial menu (Lock, Fire Phasor, Fire Torpedo, Retreat) → confirm target → 6-second resolution animation → damage report. Coordinate multi-ship attacks via alliance waypoints. | 5 min (micro-session), 20 min (coordinated fleet battle) |
| **Planet conquest** | Select attack fleet, tap target planet, choose assault type (bombardment / ground invasion), commit forces. RNG battle resolves over 30 seconds (cinematic with progress bar). Win = loot treasury + capture colony. | 10 min (battle + aftermath) |
| **Meta progression** | Upgrade ship classes (visual customization unlocks), climb seasonal leaderboard (weekly/monthly brackets), unlock tech tree nodes (faster production, stronger weapons), earn alliance prestige (cosmetic flags, monuments). | Ongoing (session-agnostic) |

### 3.2 Session-Fit Design Philosophy

**Micro (2–5 min):**
- Check notifications (production ready, under attack)
- Issue single command (move fleet, claim planet, send reinforcements)
- Glance at map (territory status, resource flows)
- Quick combat (1v1 skirmish, opportunistic ambush)

**Mid (10–20 min):**
- Multi-planet management (adjust production across empire)
- Trade optimization (analyze market, reconfigure routes)
- Fleet positioning (pre-position for upcoming battle window)
- Scouting mission (explore 5 sectors, tag high-value targets)
- Defensive response (ally under attack, coordinate counter-strike)

**Long (weekend war, 60–120 min):**
- Alliance campaign (synchronized assaults on enemy faction)
- Seasonal finale (leaderboard push, high-stakes territory grab)
- Economic warfare (blockade enemy trade lanes, starve their production)
- Diplomatic intrigue (negotiate NAPs, backstab treaties, forum drama)

**Design contract:** Every action must be completable in <30 seconds of input (tap, drag, confirm). Outcomes unfold asynchronously. Player never forced to "babysit" a progress bar—close app and return to consequences.

### 3.3 Retention Hooks

**Daily:**
- Production cycles (planets max out every ~10 hours, need harvesting to avoid waste)
- Fleet energy recharge (offline fleets regen slowly; log in to top off before battle)
- Alliance check-in (daily quest: "Scout 3 sectors for alliance" → cosmetic reward)

**Weekly:**
- Seasonal leaderboard snapshot (top 100 earn cosmetic flag, top 10 earn legendary ship skin)
- Faction war phase (Monday = scouting, Wed = skirmishes, Sat = conquest finale)

**Monthly:**
- Season rollover (fresh galaxy, new tech tree, prior season rewards distributed)
- Major content drop (new alien faction appears in neutral sectors, rare loot)

**Evergreen:**
- Revenge (your planet was raided while offline → attacker's name bookmarked → hunt them down)
- Alliance loyalty (your faction needs you for tonight's 20:00 UTC push)
- Economic dominance (corner the market on a scarce resource, profit from scarcity)

---

## 4. Progression

### 4.1 Ship Progression

**Legacy reference:** 10 ship classes (light freighter → dreadnought), 19 phasor types, 19 shield types (`GEMAIN.H:318-385`, Phase 1a §3.1).

**Modern system:**

| Tier | Class | Role | Unlock | Visual Identity |
|------|-------|------|--------|----------------|
| 1 | Scout Frigate | Exploration, speed, low combat | Starter ship | Sleek, small, civilian |
| 2 | Freighter | Trade, cargo capacity | 10k cash | Bulky hull, containers |
| 3 | Corvette | Early combat, balanced | 50k cash | Military gray, turrets |
| 4 | Destroyer | Fleet combat, torpedoes | 200k cash + Tech Node | Angular, missile racks |
| 5 | Cruiser | Heavy combat, shielding | 500k cash + Alliance Rank 2 | Thick armor, glowing shields |
| 6 | Battleship | Planetary assault, ion cannons | 1M cash + 5 planets owned | Massive, intimidating |
| 7 | Dreadnought | Flagship, command bonuses | Seasonal reward (top 50) | Unique, prestige skin |

**Customization layers:**
1. **Functional modules** (Stack Architect owns balance):
   - Engines (speed vs. energy efficiency)
   - Weapons (phasors, torpedoes, missiles—damage vs. range vs. ammo)
   - Shields (absorption vs. recharge rate)
   - Cargo bays (capacity vs. mass penalty)
2. **Cosmetic skins** (monetization):
   - Faction themes (Terran, Xeno, Pirate)
   - Seasonal exclusives (Lunar New Year dragon hull, Halloween ghost ship)
   - Alliance branding (custom decals, colors)
3. **Tech tree unlocks** (progression):
   - "Advanced Warp Coils" (+20% travel speed)
   - "Stealth Plating" (reduced detection range)
   - "Shield Harmonics" (+15% shield capacity)

**Multiple ships per player:** Own up to 10 ships (legacy `topshipno` per `WARUSR`, Phase 1a §3.2). Assign roles (exploration scout, trade hauler, combat patrol). Switch active ship instantly (no cooldown, but ships take time to travel between locations).

### 4.2 Planet / Territory Progression

**Colony tiers:**
- **Outpost** (1–2 planets): Barely self-sufficient, vulnerable
- **Barony** (3–5 planets): Stable income, can field defensive fleet
- **Sector Lord** (6–10 planets): Economic powerhouse, influence alliance strategy
- **Galactic Emperor** (11+ planets): Leaderboard contender, target for all rivals

**Planetary specialization:**
- **Mining World:** High resource richness (gold, flux pods), low environment (harsh, few men)
- **Agri-World:** High food production, supports large troop populations for conquest
- **Industrial Hub:** Balanced production (fighters, missiles, torpedoes), mid-tier everything
- **Fortress:** Max defensive bonuses (ion cannons, troops), low economic output
- **Trade Nexus:** Positioned at wormhole junction, tariff income from passing convoys

**Upgrade paths (per planet):**
- **Technology level** (0–100%): Increases production efficiency (legacy `planet.technology`, Phase 1a §3.3). Costs: research time + resources. Unlocks: advanced item types (e.g., tech 50+ required for zipper production).
- **Defenses:** Build ion cannon batteries, deploy NPC garrison fleets (costs % of production), hire mercenary patrols (cash cost).
- **Infrastructure:** Expand cargo warehouses (raise production caps), add population housing (faster men growth), construct starports (faster fleet repairs).

### 4.3 Tech Tree / Identity Progression

**Departure from legacy:** Legacy GE had flat ship class progression (bigger = better). Modern design adds lateral progression (specialization identity).

**Three tech branches:**

1. **Military** (conquest focus):
   - Weapon damage +%
   - Shield capacity +%
   - Troop training speed +%
   - Unlock: Planetary bombardment (skip ground invasion for faster conquest, but destroy stockpiles)

2. **Economic** (trade/production focus):
   - Production rate +%
   - Trade convoy speed +%
   - Cargo capacity +%
   - Unlock: Black market access (buy/sell illegal goods at premium prices, risk of NPC interdiction)

3. **Exploration** (scouting/intel focus):
   - Sensor range +%
   - Warp speed +%
   - Cloak duration +%
   - Unlock: Deep space anomalies (discover rare alien tech, high-risk PvE encounters)

**Tech points earned via:**
- Planet ownership (1 point/planet/day)
- Kills (5 points per enemy ship destroyed)
- Exploration (1 point per newly discovered sector)
- Seasonal milestones (bonus chunk at season end)

**Respec cost:** Free once per season, then escalating cash cost (prevents constant min-maxing, encourages commitment to identity).

### 4.4 Seasons & Leaderboards (Replacing Midnight Reset)

**Legacy pain point:** Midnight reset scoreboard (§6.3, Phase 1a) was arbitrary timezone-biased. Modern replacement:

**Season structure (3-month cycle):**
- **Week 1–2:** Land rush (claim best planets, form alliances)
- **Week 3–8:** Mid-season wars (territory churn, economic warfare)
- **Week 9–12:** Endgame push (leaderboard competition, high-stakes battles)
- **Season end:** Snapshot leaderboard, distribute rewards, galaxy SOFT RESETS (planets unclaimed, but players keep ships/tech/cosmetics)

**Leaderboard categories:**
- **Total Empire Value** (networth: cash + planet value + fleet value, legacy `calc_networth()`, Phase 1a §3.2)
- **Military Might** (kills + planets conquered)
- **Economic Power** (trade volume + production output)
- **Exploration** (sectors discovered + anomalies solved)
- **Alliance Glory** (top alliance by aggregate member score)

**Rewards:**
- **Top 10:** Legendary ship skin (unique, never returns)
- **Top 50:** Epic skin + exclusive tech unlock
- **Top 100:** Rare skin + cosmetic flag
- **Top 500:** Uncommon skin
- **All participants:** Season badge (bronze/silver/gold tiers based on activity)

**No hard wipes between seasons:** Players retain ship classes, tech tree progress, cosmetics. Lose territory claims (planets revert to neutral) to enable fresh competition. This balances "clean slate" excitement with respecting time investment.

---

## 5. Social / PvP / PvE

### 5.1 Alliances (Replacing Legacy Teams)

**Legacy reference:** Teams with shared `teamcode`, password-protected planet docking, pooled scores (§3.5, Phase 1a).

**Modern alliances (enhanced):**
- **Membership:** Up to 50 players per alliance (up from legacy `MAXTEAMS=50` limit on total teams). Hierarchical ranks (Leader, Officer, Member, Recruit).
- **Shared infrastructure:**
  - Alliance HQ (NPC citadel in designated sector, respawn point, shared warehouse)
  - Alliance tech pool (members contribute tech points, leadership spends on alliance-wide buffs)
  - Joint defense pacts (auto-notify all online members when allied planet attacked)
- **Coordination tools:**
  - Alliance chat (real-time, persistent history)
  - Map markers (officers can tag targets: "Strike here at 20:00 UTC")
  - Fleet formations (players can slave their ships to a commander's waypoints for synchronized jumps)
  - Shared intel (one member scouts enemy → intel auto-propagates to all alliance members in real-time)
- **Alliance vs. Alliance warfare:**
  - Territorial control score (sum of all member planets in designated war zones)
  - Seasonal alliance tournaments (bracket-style elimination, winner takes cosmetic monument in galaxy hub)

### 5.2 Open PvP Sandbox

**Core philosophy:** Galactic Empire is a **hardcore sandbox MMO**—shared universe, full-loot PvP, no instanced safe zones (except tutorial). This is the legacy identity (Phase 1a §7.2: "100% shared PvP space").

**PvP systems:**
- **Open combat:** Any player can attack any other player in space (no flagging, no consent required). Sector ownership offers no immunity (unlike EVE high-sec).
- **Full loot (modified):** Attackers loot 50% of destroyed ship's cargo (legacy §3.1 `killem()` mechanic) unless victim has insurance (§9.6 decision).
- **Revenge mechanics:**
  - Killmails (detailed battle report: attacker ship class, damage breakdown, loot dropped)
  - Bounty board (players can post bounties on rivals, hunters earn payout on kill)
  - Vendetta tracking (game tracks your attacker's location for 24 hours post-death via notification: "Your killer is in Sector 87")
- **War declarations:** Alliances can formally declare war on rival alliances, enabling special rule sets (e.g., no alliance-hopping during war, kill rewards doubled).

**Softening for mobile audience (without betraying sandbox identity):**
- **Safe Harbor docking** (§9.2 decision): Fleets docked at NPC citadels are invulnerable while offline. Cost: daily rent (% of cash) + no production. Players who want to stay "in the field" (own planets, faster growth) take risk.
- **Insurance system** (§9.6 decision): Pay upfront premium (e.g., 10k cash per week) → on death, recover 75% of cargo/ship value. Uninsured = full 50% loss (high risk, high reward for bold players).
- **Newbie grace period:** First 7 days, players respawn at tutorial station with free starter ship (no cash cost). After week 1, normal death penalties apply.

### 5.3 PvE as Gear-Up, Not Replacement

**Design stance (§9.5 decision: B hybrid):** PvP/conquest remains the spine of GE. PvE exists to provide variety, gear-up pathways, and opt-in solo content—NOT to create a safe endgame that avoids PvP.

**PvE content types:**

1. **Alien Hives** (co-op raids):
   - NPC-controlled sectors spawn Xenomorph fleets every 48 hours
   - Players (solo or alliance) attack hive, waves of NPC ships defend
   - Victory: loot rare tech blueprints, advanced weapon modules (tradeable)
   - Risk: If hive not cleared, NPCs raid nearby player planets (creating PvE threat that forces engagement)

2. **Derelict Stations** (exploration):
   - Randomly discovered in deep space (1% chance per newly scouted sector)
   - Solo mission: dock, solve light puzzle (match power conduits), loot cargo bay (gold, flux pods, cosmetic ship parts)
   - 5-minute session, no combat, pure reward for exploration

3. **Faction Patrols** (PvE combat):
   - NPC "Pirate" and "Cybertron" fleets (legacy AI from §3.6, Phase 1a) patrol neutral sectors
   - Players hunt them for cash bounties (legacy `cyb_gold` loot cap 2M)
   - Difficulty scales: Cybertrons have `cybskill 3-17` (legacy), higher skill = better AI tactics (evasion, mine-laying)

4. **Anomaly Events** (limited-time PvE):
   - Weekly event: "Wormhole Instability in Sector 200—alien artifacts detected"
   - Race (PvE and PvP mixed): First 10 players to clear NPC guardians loot legendary items
   - Creates PvPvE tension: kill NPCs or kill rival players competing for loot?

**PvE rewards feed PvP economy:** All loot is tradeable. PvE farmers supply the market with rare modules; PvP conquerors buy them to dominate wars. Symbiotic loop.

---

## 6. Session Length & Cadence

### 6.1 Hybrid Philosophy: Instant Input, Deliberate Resolution

**Legacy model (Phase 1a §2.2, §7.3):** Synchronous commands (player types `pha`, blocks for input) + asynchronous tick system (6s ship tick, 55s planet tick). World runs whether you're online or not.

**Modern adaptation:**
- **Player experience:** Instant responsiveness (tap Fire → immediate UI feedback, satisfying sound effect, weapon animation starts)
- **World resolution:** Deliberate strategic timing (damage applies after 6-second calculation, allowing target to react: raise shields, activate cloak, flee)
- **No blocking waits:** Client never shows spinner/progress bar exceeding 2 seconds. Instead: submit command → close app → push notification with result ("Your torpedo destroyed Enemy Dreadnought—2M gold salvaged")

**Why preserve 6-second combat cadence?**
1. **Tactical depth over twitch reflex:** Players have time to coordinate (alliance chat: "I'll fire torpedo at :05, you fire at :10 to overwhelm shields"). Not about APM; about positioning and timing.
2. **Mobile-friendly:** 6 seconds is long enough to issue a command during a stoplight, subway ride, bathroom break. Twitch combat (1-second reaction windows) hostile to mobile context.
3. **Network tolerance:** Mobile connections drop/lag. 6-second server ticks smooth over packet loss without rubber-banding.
4. **Respects legacy identity:** GE vets expect strategic pacing (Phase 1a design pillar: "keep strategic fleet/conquest meta, kill BBS I/O"). We modernize the interface, not the core tempo.

### 6.2 Production Cycles (55-Second Tick)

**Legacy reference:** `PLANTIME = 55` seconds, `multiply()` production function (Phase 1a §3.3, `GEPLANET.C:195`).

**Modern implementation (Client UX owned):**
- **Backend:** Preserve 55-second server tick for production (balance proven over decades of legacy GE play)
- **Frontend:** Mask the tick with progress bars:
  - Planet screen shows: "Fighters: 42/100 (ETA 38s)" with smooth animated bar
  - Push notification on cap: "Planet Forge-7: Fighter production maxed (100/100). Harvest now!"
- **Player perception:** Feels continuous (not tick-y). Every ~1 minute, satisfying "ding" of resources ready.

**Why 55 seconds?**
1. **Engagement pacing:** Too fast (<30s) = feels grindy (constant babysitting). Too slow (>2min) = boring (no micro-session payoff).
2. **Strategic resource scarcity:** 55s tick rate means ~65 production cycles per hour. A planet making 10 fighters/tick generates 650 fighters/hour. Balances supply (enough to sustain combat) vs. scarcity (can't spam infinite fleets).
3. **Async-friendly:** A player who checks in every 10 minutes harvests ~11 ticks of production (satisfying chunk). A player who ignores planets for 2 hours hits cap and wastes overflow (light punishment for neglect, not catastrophic).

### 6.3 Travel Time & Warp Mechanics

**Legacy reference:** Ships move via `moveship()` every 6s tick, `coord += speed * sin(heading)`, max speed ~9999 warp (Phase 1a §3.1 physics model).

**Modern abstraction:**
- **Short trips (1–5 sectors):** Instant warp (tap destination → ship arrives in 2 seconds, client animation). No need to micro-manage impulse/rotation for local moves.
- **Long trips (6–20 sectors):** Auto-pilot queue (tap destination → "ETA 90 seconds" → close app → push notification on arrival). Client shows warp trail animation if player watches.
- **Strategic travel (21+ sectors):** Wormhole network (legacy `GALWORM`, Phase 1a §3.4). Discover wormholes via exploration, use for instant cross-galaxy jumps. Wormhole sectors = PvP hotspots (ambush opportunities).

**Energy costs (legacy `ACCENGAMT=120/tick`, `ROTENGUSE=30/tick`):**
- Preserve concept (warp costs energy), but simplify: flat 10% energy per long-distance warp. Ships regenerate 1% energy per minute while idle (docked or stationary). Full recharge = ~100 minutes offline, or instant at NPC refuel station (costs cash or flux pods).

**Why not real-time ship piloting?**
- Mobile context: players can't steer ships with joystick during commute. Auto-pilot respects mobile UX.
- Preserve option for manual control: "Tactical mode" toggle for players who want to micro (drag to set heading/speed, legacy-style). Power-user feature, not mandatory.

### 6.4 Push Notifications (Anti-BBS Polling)

**Legacy pain point (Phase 1a §7.6):** BBS clients polled every 6s for updates (tick system). Drains battery, hostile to mobile.

**Modern solution:** Event-driven push notifications:

| Event | Notification Trigger | Example Message |
|-------|---------------------|----------------|
| Under attack | Enemy enters sector with your planet/fleet | "ALERT: Sector 42 under attack by [Rival]! Defend now." |
| Production ready | Planet stockpile hits cap | "Colony Delta-9: Gold reserves full (5000/5000). Harvest now!" |
| Fleet arrived | Auto-pilot travel complete | "Scout Fleet: Arrived at Sector 127. 3 planets detected—claim?" |
| Combat result | 6-second combat tick resolves your action | "Torpedo hit! Enemy Cruiser destroyed. 1.2M gold salvaged." |
| Alliance ping | Officer marks target or requests aid | "[AllianceLeader]: All hands, strike Sector 99 at 20:00 UTC!" |
| Seasonal milestone | Leaderboard position change | "You've entered Top 100! (Rank #87). Keep pushing!" |

**Notification settings (player control):**
- Critical only (under attack, fleet destroyed)
- Standard (+ production ready, alliance pings)
- Full (+ every combat result, market price changes)

**Server architecture (Stack Architect owned):** Websocket connection while app open (real-time updates), APNS/FCM push when app backgrounded. Event queue persists if notifications fail (re-deliver on next app open).

---

## 7. Keep / Transform / Kill (Designer Lead)

Phase 1a provided a preliminary analysis (§8). Here's the **locked Designer stance** for Phase 1b—definitive calls on what survives modernization.

### 7.1 ✅ KEEP (Modernize, Preserve Core)

| System | Designer Rationale | Modernization Notes |
|--------|-------------------|---------------------|
| **Strategic fleet/conquest loop** | The soul of GE. Players build empires, not solo hero narratives. Territory control = status. Planetary economy = long-term investment. This is the "EVE on mobile" fantasy. | Keep loop structure (explore → claim → produce → conquer). Reduce friction: auto-trade routes, batch planet commands, alliance coordination tools. |
| **6-second combat cadence** | Tactical pacing without twitch reflex. Time to coordinate multi-ship attacks ("I'll fire at :05, you at :10"). Mobile-friendly (issue command during micro-session). Proven by 30+ years of legacy play. | Keep server-side 6s tick. Client masks with animations (phasor beam charges over 3s, fires at 6s mark, impact at 6s). Feels fluid, not turn-based. |
| **55-second production tick** | "Empire building" tempo. Frequent enough for micro-session payoff (check in every 10 min, harvest progress), slow enough to avoid babysitting grind. | Keep tick rate. Add progress bars, ETA timers, push notifications to mask discrete ticks. Perception = continuous production. |
| **Permadeath for ships (not accounts)** | Stakes create meaning. Losing 50% cargo on death fuels revenge loops, alliance solidarity ("they killed me, help me retaliate"). Without loss, PvP is meaningless. | Keep 50% cargo loss. Add insurance system (§9.6) to soften for casuals without eliminating stakes. |
| **Open PvP sandbox** | GE's identity = hardcore conquest. Shared universe, full loot, no instanced safe zones. Niche but fiercely loyal audience (EVE, Albion). | Keep no-consent PvP. Add Safe Harbor docking (§9.2) as opt-in protection, not default. Separate Hardcore shard later (no Safe Harbor, for masochists). |
| **Planetary production economy** | Long-term investment (claim planet → set production rates → harvest wealth over days). Creates empire depth beyond combat. Legacy `multiply()` formula (environment × resource × tech) is elegant. | Keep formula, expose it to players via tooltips ("This planet's 9/9 environment + 7/9 resource = +145% production rate"). Gamify optimization. |
| **Fog of war (sector vision)** | Limited intel creates scouting value, stealth gameplay (cloak), and "ambush at wormhole" tactics. Total vision = homogenizes strategy. | Keep sector-based vision. Add "Intel" resource (spy reports, alliance sensor network) as progression unlock. |
| **Team/alliance warfare** | Social = retention. Coordinated attacks, shared planets, alliance chat = why players stay for years. | Expand: alliance tech pool, joint defense pacts, territory control scoring, seasonal tournaments. |

### 7.2 🔄 TRANSFORM (Rework, Preserve Intent)

| System | Legacy Problem | Modern Solution |
|--------|---------------|-----------------|
| **Text command parser** | 3-letter abbreviations (`pha`, `torp`, `buy`) hostile to mobile. Arcane for new players. Relic of BBS text efficiency (save modem bandwidth). | **Replace entirely:** Visual UI (tap ship → radial menu: Fire / Scan / Transfer / Retreat). Context-aware buttons (hide "Buy" unless docked). Preserve power-user shortcuts via gesture library (swipe right on enemy = quick-fire phasor). |
| **Tick polling system** | BBS clients polled every 6s (legacy `rtkick()`). Drains battery, not scalable. | **Event-driven server:** Commands queued instantly, server resolves at 6s intervals, pushes results via websocket. Client interpolates between ticks (smooth animations). No polling. |
| **Offline vulnerability** | Players lose planets while AFK (cyborgs attack, rivals raid). Toxic for mobile (can't defend 24/7). Legacy §7.6 identifies this as breakpoint. | **Safe Harbor + NPC defenders (§9.2 decision):** Dock fleets at NPC citadels (invulnerable, costs rent). Or hire NPC garrison for planets (costs % production). Strategic choice: pay for safety vs. stay in field for growth. |
| **Ship combat (manual aim)** | Legacy phasors require manual heading adjustment (`degrees` offset). Fun for BBS text nerds, tedious on mobile. | **Auto-aim default + manual option:** Tap target → auto-locks optimal angle. Advanced players toggle "Manual Aim Mode" (drag to aim, +15% damage bonus for skill). Power-user opt-in, not mandatory. |
| **Planet conquest (pure RNG)** | Legacy `attack_men()` is RNG loop (Phase 1a §5.2): random rolls decide victor. No player agency once assault starts. | **Tactical layer (optional):** Deploy troops in waves (choose flanking vs. frontal assault, call orbital strike for +20% attacker bonus but costs ship energy, time reinforcements). Or keep RNG but show odds pre-battle (XCOM-style: "78% victory chance") so players make informed bets. |
| **Trade economy (fixed prices)** | Legacy prices set per planet by owner, no supply/demand. Exploit: buy low at own planet, sell high at ally's marked-up planet, infinite arbitrage. | **Dynamic pricing:** Planet buy price rises when stockpile low, falls when high (supply/demand). Add random events ("Plague on Planet X reduces Men, spiking Food prices"). Arbitrage still viable but requires market timing. |
| **Mail system (async alerts)** | Legacy sent BBS mail for alerts (planet attacked, production maxed). Read via separate MajorBBS mail interface—clunky. | **In-app inbox + push notifications:** Real-time alerts (push), persistent inbox (tap to read, swipe to delete), quick-reply actions ("Send Reinforcements" button in attack notification). Unified UX. |
| **Universe size (30×15 grid)** | 450 sectors too small for 1000+ players. Land rush favors early adopters; late joiners stuck with garbage planets. Phase 1a §9.1 flags this. | **Instanced shards (§9.1 decision):** Each shard sized ~100×50 (5000 sectors), target 500–1000 players/shard. Density for faction wars without dilution. Cross-shard portals for rare prestige events (top 10 alliances per shard compete in neutral arena). |
| **Midnight reset scoreboard** | Arbitrary timezone bias (midnight EST?). Daily resets punish wrong-TZ players. Phase 1a §6.3. | **Seasonal leaderboards (§4.4):** Weekly/monthly snapshots, 3-month seasons. Rewards distributed at season end. No daily resets. Rolling competition, fair to all timezones. |

### 7.3 ❌ KILL (Remove, Anti-Fun or Obsolete)

| System | Why Kill | No Replacement Needed |
|--------|----------|----------------------|
| **BBS session blocking (text input loop)** | Commands block until user types response. Mobile expects instant feedback. Legacy §7.6 breakpoint. | Async-first design: tap button → action queued → close app. No blocking. |
| **Single-threaded architecture** | Legacy `main()` event loop processes ships sequentially. Cannot scale to 1000+ concurrent users. | Microservices (Stack Architect owned): combat server, economy server, chat server, load balancer. |
| **Btrieve database** | 1980s flat files, no relational queries, fragile. | PostgreSQL (Stack Architect choice): ACID, JSON support, horizontal scaling. |
| **3-letter command abbreviations** | `imp` = impulse, `pha` = phasor, `buy` = purchase. Arcane jargon, hostile to new players. | Icon-based UI. Buttons labeled "Fire Phasor" with weapon thumbnail. No abbreviations. |
| **Cyborg AI throttling** | Legacy processed 2 cyborgs/second to avoid BBS lag (`CYBMAXPERTICK=2`). Artificially limits NPC challenge. | Remove throttle. Process all NPCs in parallel (async tasks). Scale NPC density for challenge. |
| **Spy mechanics (as-is)** | Legacy: 1-in-10 chance per 55s tick to get intel, random error in report. Too opaque, too rare. | Kill RNG spy. Replace with deterministic: "Plant spy → guaranteed intel after 10 minutes, capture risk scales with planet security rating." Or cut spies entirely if not fun in playtesting. |
| **Manual sector-by-sector navigation** | Legacy: type `imp 9` to go 9 warp, type `rot 45` to turn 45°. Tedious for cross-galaxy travel. | Auto-pilot (tap destination → ETA timer). Instant for local (<5 sectors), queued for distant. Manual mode = power-user opt-in. |

---

## 8. Answers to Phase 1a's 7 Decisions

Phase 1a §9 posed seven open questions. Here are the **locked Phase 1b design picks**:

### 8.1 Universe Size & Topology (Phase 1a §9.1)

**Decision: D (instanced galaxies / shards), sized per B (~100×50 sectors, ~5000 sectors total), target 500–1000 concurrent players per shard. Add cross-shard portals for rare prestige events.**

**Rationale:**
- **Why shards (D)?** Scalability. A single 30×15 universe (legacy 450 sectors) dies with 1000 players—land rush favors first 100, rest quit. Infinite procedural (C) dilutes PvP density (players spread thin, never collide). Shards balance: each shard feels full (faction wars, territory conflict) without server overload.
- **Why 100×50 per shard (B-sized)?** 5000 sectors supports 500–1000 empires at healthy density (~5–10 sectors/player average at equilibrium, accounting for neutral/contested zones). Larger (e.g., 200×100 = 20k sectors) risks dilution again. Smaller (30×15 legacy) repeats land-rush problem.
- **Cross-shard portals:** Top 10 alliances per shard (by seasonal leaderboard) unlock "Nexus Wormhole" access for 48-hour cross-shard raid event. Loot legendary cosmetics. Creates prestige incentive (be best on your shard to compete globally) without fracturing community day-to-day.
- **Shard identity:** Each shard gets unique name (Galaxy Andromeda, Galaxy Fornax, etc.), persistent across seasons. Alliances build shard reputation ("Andromeda's strongest faction"). Players can reroll to new shard once per season (costs cosmetic currency) if they hate their shard's politics.

**Handoff to Stack Architect:** Shard infrastructure must support:
- 500–1000 simultaneous websocket connections per shard
- Separate database per shard (shard isolation for lag tolerance)
- Cross-shard event queues for Nexus portal battles

---

### 8.2 Offline Protection (Phase 1a §9.2)

**Decision: B + C hybrid (Safe Harbor docking as default NPC protection + optional Hire NPC Defenders for planets). Reject D (no protection) for default servers. Optional Hardcore shard later with zero protection.**

**Rationale:**
- **Why hybrid B+C?** Mobile players cannot defend 24/7. Pure no-protection (D) bleeds casual audience—you wake up to empire destroyed, quit game. But full immunity (A) eliminates stakes (why even have PvP?). Hybrid: players choose risk tolerance.
- **Safe Harbor (B) for fleets:**
  - NPC citadels in every 10th sector (50 citadels across 100×50 shard). Dock fleet → invulnerable while offline.
  - Cost: Daily rent (1% of fleet value per day, e.g., 10k cash/day for 1M-cash fleet) OR accept "docking tax" (citadel takes 5% of your next trade profit).
  - Strategic tradeoff: Pay rent for safety, or stay deployed in field (faster response to opportunities, but risk getting jumped).
- **Hire NPC Defenders (C) for planets:**
  - While offline, hire NPC garrison fleet to patrol your planet (costs 10% of planet's daily production).
  - NPC strength scales with payment: basic garrison defends vs. solo attacker, premium garrison defends vs. 3-ship assault.
  - Cannot defend vs. coordinated alliance attack (10+ ships). By design: organized conquest beats solo turtling.
- **Why reject full D (no protection)?** Tested in legacy GE—hardcore but niche. Phase 1b targets broader mobile audience first. Hardcore shard launches later (Season 3+?) for masochists.

**UX handoff:** Tutorial MUST explain Safe Harbor during first logout: "Dock your fleet at Citadel Alpha before closing app, or risk attack while offline. Yes, enemies are real players—they don't sleep!"

---

### 8.3 Combat Pacing (Phase 1a §9.3)

**Decision: A (keep ~6-second strategic tick for fleet combat MVP). Realtime skirmish mode deferred (optional later). Matches product lock (strategic fleet/conquest, not twitch).**

**Rationale:**
- **Why 6s?** (See also §6.1 for full justification)
  1. **Tactical, not twitch:** Allows coordination (alliance voice chat: "Fire at :08 mark"), positioning (flee/cloak/shield before next volley), and strategy (bait opponent into wasting torpedo). APM is not skill; timing and positioning are.
  2. **Mobile context:** Players issue commands during stoplights, subway rides, waiting rooms. Twitch combat (sub-1s reaction) hostile to mobile multitasking.
  3. **Network resilience:** Mobile networks have 100–500ms latency spikes. 6s server ticks absorb jitter without rubber-banding.
  4. **Legacy identity:** GE vets expect this pacing. Changing to real-time betrays brand.
- **Why defer realtime mode?** Product focus = strategic conquest (spec lock). Realtime skirmish (1v1 twitch duels) is fun but scope creep for MVP. Add post-launch if metrics show demand ("Arena Mode" PvP with realtime controls, bet cosmetics on duels).
- **Implementation (Stack handoff):** Combat server runs 6s tick loop, queues player actions (fire, shield, cloak), resolves damage at tick boundary, broadcasts results via websocket. Client interpolates (phasor beam animates over 6s, torpedo travels smoothly, shield ripple on hit).

**UX anti-pattern warning:** Do NOT show "6-second countdown timer" on screen (feels turn-based/boring). Instead: instant UI feedback (tap Fire → phasor charges with satisfying sound/animation), outcome arrives 6s later (feels real-time with strategic weight).

---

### 8.4 Monetization (Phase 1a §9.4)

**Decision: B (F2P + cosmetics only, no P2W). No production speedups that buy power. Cosmetic ships/planets/empire brands OK. Subscription (D) may be explored later as Cosmetics+QoL (not power).**

**Rationale:**
- **Why F2P?** Broadest audience. Mobile MMOs die behind $10 paywall. F2P proven by successful comp (Albion Online mobile, EVE Echoes pre-P2W pivot).
- **Why cosmetics-only?** PvP sandbox requires fair competition. Selling production speedups (pay to produce 2x fighters/hour) = P2W = death spiral (whales dominate, F2P quit, whales fight each other, churn). GE's appeal = strategic skill, not wallet.
- **What cosmetics?**
  - **Ship skins:** Faction themes (Terran military gray, Xeno biotech purple, Pirate rust), seasonal (Halloween ghost ship, Lunar New Year dragon), prestige (top 10 seasonal reward).
  - **Planet cosmetics:** City skyline variants (cyberpunk neon, desert outpost, ice fortress), orbital rings, moons.
  - **Empire identity:** Custom flag/emblem, alliance monument skins, HUD color themes.
  - **Animations:** Weapon VFX (phasor beam colors, torpedo trails), warp effects (standard blue warp vs. premium rainbow shimmer).
  - **Emotes / taunts:** Post-kill emote (optional gloat for trash talk).
- **Subscription consideration (later):** "Admiral's Pass" ($5/mo): all cosmetics unlocked, +1 extra ship slot, priority queue during peak hours, exclusive monthly skin. **No gameplay power.** Test this Season 3+ if cosmetic-only revenue underperforms.

**Red lines (NEVER monetize):**
- Production speedups (e.g., "2x planet output for 24h")
- Combat power (e.g., "+20% weapon damage boost")
- Energy/cargo (e.g., "instant fleet energy refill")

**Handoff to LiveOps:** Seasonal cosmetic shop rotation (new skins every 2 weeks), flash sales (20% off prestige skin for 48h), battle pass (free track + premium track, all cosmetic rewards).

---

### 8.5 PvE vs PvP Balance (Phase 1a §9.5)

**Decision: B (hybrid). PvP/conquest remains the spine; add optional PvE sectors (alien hives, derelicts, co-op objectives) that feed materials/tech into the conquest economy without creating a pure safe endgame that invalidates PvP.**

**Rationale:**
- **Why hybrid?** Pure PvP (A) is niche—many mobile players want variety, not relentless combat. Pure PvE (reject) betrays GE identity (sandbox conquest). Hybrid: PvE as side content, not replacement.
- **PvE design principles:**
  1. **No safe farming endgame:** PvE sectors are neutral zones (no planet claims), so PvE farmers cannot turtle indefinitely. To profit from PvE loot, must return to PvP zones (risk of ambush on trade route).
  2. **PvE loot feeds PvP economy:** Alien hive drops = rare tech blueprints (tradeable), advanced weapon modules (tradeable). PvE farmers supply market; PvP conquerors buy modules to dominate wars. Symbiotic.
  3. **PvE as variety, not grind:** 10-minute co-op mission, not 2-hour dungeon slog. Mobile session fit.
- **Specific PvE content (§5.3 details):**
  - **Alien Hives:** Co-op raids (5 players recommended), waves of NPC ships, loot rare tech. Hives respawn every 48h, creating scheduled events (alliance coordinates hive clear).
  - **Derelict Stations:** Solo exploration (5-min light puzzle), loot gold + cosmetic parts. No combat, pure reward for scouting.
  - **Anomaly Events:** Weekly limited-time PvPvE (kill NPCs or kill rival players competing for loot). Tension = cooperation vs. backstab.
- **Why not separate PvE/PvP servers?** Fragments community. Hybrid keeps all players in same economy (PvE farmers sell to PvP fighters).

**Metrics to watch post-launch:** If >40% of playtime is PvE, PvE is cannibalizing PvP (bad). Rebalance: reduce PvE loot drop rates, increase PvE difficulty, gate best loot behind PvP (e.g., "Alien Queen drops legendary module, but only spawns in contested PvP sectors").

---

### 8.6 Death Penalty (Phase 1a §9.6)

**Decision: C (insurance system). Pay upfront premium to recover majority of cargo/outfit on death. Uninsured = legacy 50% loss (high stakes). Starter/tutorial ships soft-protected (free respawn for first 7 days).**

**Rationale:**
- **Why insurance?** Balances casual (soft death penalty) vs. hardcore (full stakes). Adds strategic choice: pay safety cost vs. gamble.
- **Insurance mechanics:**
  - **Cost:** 10k cash per week (flat rate, regardless of fleet value). Or 1% of fleet value per week (scales with wealth).
  - **Benefit:** On death, recover 75% of cargo (instead of losing 50% to loot). Ship respawns at Safe Harbor citadel with 75% of pre-death cargo intact. 25% still lost (dropped as salvage for attacker).
  - **Uninsured:** Legacy 50% loss (high risk, high reward for bold players who don't want to pay weekly premium). Attacker loots 50% of cargo.
- **Starter protection:** First 7 days post-account creation, all ships auto-insured (100% recovery, free respawn at tutorial station). After week 1, must buy insurance or go uninsured.
- **Why not full permadeath (D account wipe)?** Too punishing for mobile. Players invest weeks building empire; losing everything to one gank = uninstall. Ship permadeath (lose fitted modules, respawn with basic ship) is harsh enough.
- **Why not trivial penalty (10% loss)?** Eliminates stakes. PvP becomes meaningless if victim loses pocket change. 25–50% loss = significant pain, fuels revenge ("they took 1M gold, I'm hunting them down").

**UX flow:**
1. Player dies (ship destroyed in PvP)
2. Death screen shows:
   - **Insured:** "Your insurance recovered 75% of cargo. Respawning at Citadel Alpha. [View Killmail] [Revenge]"
   - **Uninsured:** "You lost 50% of cargo (1.2M gold looted by [Attacker]). [View Killmail] [Revenge] [Buy Insurance?]"
3. Revenge button tracks attacker for 24h (shows their location on map, incentivizes counter-strike).

**Handoff to Economy Designer:** Balance insurance cost vs. average death frequency. Target: insurance should cost ~10% of one death's loss (so dying >10 times/week, insurance is worth it; dying <10 times, risk it uninsured).

---

### 8.7 Real-Time vs Turn Identity (Phase 1a §9.7)

**Decision: A (hybrid strategic real-time). Commands feel instant (UI responsive, no blocking); world resolves on deliberate cadence (6s combat, 55s production). Not full twitch, not daily Civ turns.**

**Rationale:**
- **Why hybrid?** Unique market positioning. Mobile MMO competitors are either:
  - **Real-time twitch** (e.g., EVE Echoes manual piloting): High skill ceiling, but exhausting (can't play during commute).
  - **Slow turn-based** (e.g., Civilization async MP): Low time pressure, but boring (waiting hours for opponent's turn).
- **GE hybrid = "strategic real-time":** Fast enough to feel alive (world updates every 6–55s, not daily), slow enough to be thoughtful (coordinate alliance attacks, position fleets, not frantic APM spam). Perfect for mobile: issue orders during micro-session, check consequences later.
- **Instant command input:** Tap Fire → UI responds in <100ms (button highlight, sound effect, weapon charges). No blocking waits. Player feels in control.
- **Deliberate world resolution:** Damage applies at 6s tick (target can react: raise shields, flee, cloak). Production completes at 55s tick (resource scarcity, not instant gratification). Strategic weight.
- **Marketing angle:** "Command an empire, not a joystick." Appeals to older demographic (30–50 age, nostalgia for legacy GE, less twitch reflex, more strategic thinking). Differentiates from Fortnite/PUBG mobile twitch crowd.

**Contrasts:**
| Aspect | GE Hybrid | Real-Time Twitch | Turn-Based |
|--------|-----------|------------------|------------|
| Input | Instant (tap) | Instant (joystick) | Delayed (submit turn) |
| Resolution | 6s tick | Frame-by-frame (60 FPS) | Hours/days |
| Skill | Positioning, timing | APM, reflex | Long-term planning |
| Session | 2–20 min | 20–60 min | Async (check daily) |

**Handoff to Client UX:** UI must feel instant (button feedback <100ms), but communicate strategic pacing (e.g., phasor charges over 3s animation, fires at 6s mark, damage number pops at 6s). Tutorial explains: "Combat is strategic, not twitch. Time your shots, coordinate with allies."

---

## 9. Mobile "Empire" UX Contract (For Client UX Handoff)

This section defines what MUST be on-screen vs. deep menus, push notification triggers, and anti-patterns to avoid. Client UX owns wireframes; this is the design spec.

### 9.1 HUD (Always Visible)

**Portrait mode (default, one-handed use):**
- **Top bar:**
  - Cash balance (gold icon + number, e.g., "1.2M")
  - Fleet energy (lightning icon + %, e.g., "85%", red if <20%)
  - Active ship thumbnail (tap to switch ships)
  - Alliance badge (tap to open alliance screen)
  - Settings gear icon
- **Center:**
  - Contextual action button (large, thumb-reachable):
    - In space: "Scan Sector"
    - Docked at planet: "Manage Colony"
    - In combat: "Fire Phasor"
  - Mini-map (10% of screen, bottom-right): shows current sector + adjacent 8 sectors, your ship (blue dot), allied ships (green), enemy ships (red), planets (white circles)
- **Bottom nav bar (4 icons):**
  - **Map** (galaxy view, claim planets, wormholes)
  - **Fleet** (ship loadout, travel, combat history)
  - **Empire** (planet list, production dashboard, trade routes)
  - **Social** (alliance chat, inbox, leaderboard)

**Landscape mode (optional, for "tactical combat view"):**
- Full-screen sector view (3D or stylized 2D, ships as icons)
- Weapon radial menu (right side): Phasor, Torpedo, Missile, Shields, Cloak
- Target list (left side): Enemy ships in sector, tap to lock
- Combat log (bottom ticker): "You fired Phasor → 12k damage to [Enemy]. Enemy shields down!"

### 9.2 Deep Screens (Tap to Access)

**Map Screen (tap "Map" icon):**
- Zoomable galaxy grid (pinch to zoom, drag to pan)
- Overlay toggles: "My Territory" (highlight your planets), "Alliance Territory", "Neutral", "Threats" (enemy fleets detected)
- Tap sector → detail panel: planets (tap to inspect), fleets present (tap to engage), wormholes (tap to warp)

**Fleet Screen (tap "Fleet" icon):**
- Ship roster (swipe horizontally to browse your 10 ships)
- Per-ship: name, class, current location, cargo, damage %, energy %
- Tap ship → detail: loadout (weapon/shield/engine modules), travel history, combat log (killmail list)
- "Repair" button (if docked), "Travel" button (set destination)

**Empire Screen (tap "Empire" icon):**
- Planet list (vertical scroll, 1 card per planet):
  - Planet name, sector coords, production status (e.g., "Gold: 3200/5000, ETA 8m")
  - Alert badge if under attack or production maxed
- Tap planet → management panel:
  - Production sliders (Men, Food, Fighters, Gold, etc., sum to 100%)
  - Treasury (cash on hand, withdraw to personal cash)
  - Defenses (ion cannons, garrison fleet status)
  - "Attack" button (if not your planet)

**Social Screen (tap "Social" icon):**
- **Alliance tab:** Member roster, alliance chat, alliance tech pool (contribute/spend points), territory map
- **Inbox tab:** Notifications history (attack reports, spy intel, trade confirmations, seasonal rewards)
- **Leaderboard tab:** Filters: Total Empire, Military, Economic, Exploration. Season snapshot vs. all-time.

### 9.3 Push Notification Triggers (Must Implement)

| Trigger | Notification Text | Action |
|---------|------------------|--------|
| Under attack (fleet) | "ALERT: Your fleet in Sector 42 is under attack by [Rival]!" | Tap → open Map, jump to Sector 42, "Defend" button |
| Under attack (planet) | "ALERT: Colony Delta-9 under siege! Defenders: 60% strength." | Tap → open Empire screen, planet detail, "Send Reinforcements" |
| Production ready | "Colony Forge-7: Fighter production maxed (100/100). Harvest now!" | Tap → open Empire screen, planet detail, "Harvest" button (instant collect) |
| Fleet arrived | "Scout Fleet arrived at Sector 127. 3 planets detected—claim?" | Tap → open Map, Sector 127 detail |
| Combat result | "Victory! Your torpedo destroyed [Enemy Cruiser]. Salvaged 1.2M gold." | Tap → view killmail (detailed battle report) |
| Alliance ping | "[AllianceLeader]: All hands, strike Sector 99 at 20:00 UTC!" | Tap → open Alliance chat, map marker auto-placed |
| Seasonal milestone | "You've entered Top 100! (Rank #87). Season ends in 3 days!" | Tap → open Leaderboard |
| Insurance expired | "Your fleet insurance expires in 24 hours. Renew now?" | Tap → open Fleet screen, "Buy Insurance" button |

**Notification settings (player control):** Critical (attacks, deaths), Standard (+production, alliance), Full (+market, every combat tick).

### 9.4 Anti-Patterns (DO NOT IMPLEMENT)

| Anti-Pattern | Why Bad | Correct Approach |
|--------------|---------|------------------|
| **BBS text menus** | "Press 1 for Map, 2 for Fleet, 3 for Empire..." Hostile to touch UI. | Icon-based nav bar (Map, Fleet, Empire, Social). |
| **3-letter commands as primary** | `pha`, `torp`, `buy` = arcane jargon. | Buttons with full labels + icons ("Fire Phasor" + phasor thumbnail). Power-user console optional. |
| **Spinner/progress bars >2s** | Feels slow, breaks mobile flow. | Submit command → close app → push notification with result. |
| **Forced tutorial >3 minutes** | Mobile players skip/quit if tutorial drags. | Interactive 90-second tutorial: "Tap to fire phasor → destroy tutorial drone → claim your first planet. Done!" Skip button after 30s. |
| **Tiny tap targets (<44px)** | Mobile thumb accuracy. | Minimum 44×44px buttons (Apple HIG standard). |
| **Modal popups blocking gameplay** | "Daily reward!" popup covers HUD. | Non-intrusive banner (top of screen, auto-dismiss after 3s, tap to view detail). |
| **No haptic feedback** | Combat feels weightless. | Haptic on: weapon fire, torpedo hit, shield impact, planet claimed. |

### 9.5 Accessibility (Must Support)

- **Colorblind modes:** Red/green combat indicators also use shapes (red = triangle down, green = triangle up).
- **Font scaling:** Support iOS/Android system font size settings (HUD text scales 100–150%).
- **One-handed mode:** All primary actions reachable by thumb in portrait mode (no top-left buttons for critical actions).
- **Voice chat integration:** Alliance voice channel (opt-in, push-to-talk) for coordinated attacks.

---

## 10. Collaboration Notes (What Comes Next)

### 10.1 For Client UX Team (Wireframes / Prototypes)

**Your deliverable (Phase 1c):** Wireframes for:
1. **HUD (portrait mode):** Top bar, center action button, mini-map, bottom nav. Annotate tap targets, modal flows.
2. **Galaxy Map screen:** Zoomable grid, sector detail panel, planet inspection, fleet engagement flow.
3. **Empire dashboard:** Planet list cards, production sliders, treasury/defenses panel.
4. **Combat view (landscape mode):** Sector tactical view, weapon radial menu, target list, combat log.
5. **Onboarding tutorial:** 90-second flow (fire phasor → claim planet → intro to Safe Harbor).

**Open questions for UX:**
- **Visual style:** Sci-fi realism (EVE-style dark, gritty) vs. stylized (Rebel Inc. clean, iconographic)? Recommend stylized for mobile readability.
- **Animation budget:** How much interpolation between 6s combat ticks? (e.g., phasor beam charges over 3s, fires at 6s, impact particle effects?). Balance: satisfying feedback vs. battery drain.
- **Portrait vs. landscape priority:** Default portrait (one-handed commute play), landscape opt-in for serious combat sessions?

**Dependency:** Needs Phase 1b approval (this doc) before starting wireframes.

### 10.2 For Stack Architect (Backend Systems)

**Your deliverable (Phase 1d):** Architecture doc covering:

1. **Shared persistent galaxy per shard:**
   - Database schema (sectors, planets, ships, users)
   - Shard isolation (separate DB per shard? Shared DB with shard_id partitioning?)
   - Cross-shard event queue (for Nexus portal battles)

2. **Event-driven updates:**
   - Websocket server (broadcast sector state changes to all clients in sector)
   - Push notification service (APNS/FCM integration)
   - Event queue architecture (combat actions, production ticks, fleet movement)

3. **Combat resolution (6s tick):**
   - Server tick loop (process all combat actions in queue, resolve damage, broadcast results)
   - Client interpolation (smooth animations between ticks)

4. **Reconnect mid-combat:**
   - Stateless combat (server-authoritative, client can reconnect and sync current combat state)
   - Grace period (if client disconnects, ship continues auto-defense for 30s before fleeing)

5. **Offline Safe Harbor state:**
   - Docked fleets marked invulnerable in DB
   - NPC garrison fleets (AI defender spawn/despawn logic)

6. **Seasons:**
   - Leaderboard snapshot service (weekly/monthly/seasonal)
   - Soft reset (planets unclaimed, ships/tech/cosmetics persist)
   - Reward distribution queue

**Open questions for Stack:**
- **Tech stack confirmation:** FastAPI (REST + websockets), PostgreSQL, Redis (state cache), Docker/Kubernetes? Confirm or propose alternatives.
- **Horizontal scaling:** Load balancer strategy (shard-sticky sessions? Round-robin per sector?). Target: 1000 concurrent users per shard, 10 shards = 10k total capacity.
- **Latency targets:** <200ms for command submission (tap Fire → server ACK), <50ms for websocket state broadcast (combat result → all clients in sector). Confirm feasible.

**Dependency:** Needs Phase 1b approval + Client UX wireframes (to validate data flows).

### 10.3 For Economy Designer (Balance Tuning)

**Your deliverable (Phase 2):** Spreadsheet model for:
- Planet production rates (balance 55s tick output vs. consumption, prevent runaway inflation)
- Ship upgrade costs (ensure 10k starter → 1M dreadnought requires ~50 hours of progression, not 500 or 5)
- Death penalty (insurance cost vs. average death frequency, target 10% of one death's loss per week)
- Tech tree costs (balance Military vs. Economic vs. Exploration branches, no dominant strategy)

**Dependency:** Needs Phase 1b approval (this doc locks core systems to tune).

### 10.4 For LiveOps / Monetization (Post-Launch)

**Your deliverable (pre-launch):** Cosmetic shop catalog (50+ launch skins: 10 ship skins, 10 planet cosmetics, 10 flags, 10 weapon VFX, 10 warp effects). Pricing strategy ($2–$10 per skin, seasonal bundles).

**Your deliverable (post-launch):** Seasonal event calendar (alien hive spawn schedule, cross-shard Nexus events, cosmetic shop rotations).

---

## 11. Open Risks / Follow-Ups

### 11.1 Remaining Ambiguities (Resolve in Playtesting)

| Risk | Impact | Mitigation |
|------|--------|------------|
| **6s combat feels too slow on mobile** | Players perceive as "laggy" vs. instant-gratification mobile games. | Playtest with 10-player alpha (Week 8). If feedback is "boring," reduce to 3s tick (but preserve strategic pacing, not twitch). Fallback: offer "Blitz Mode" (1s tick) as separate queue. |
| **Offline Safe Harbor too safe** | If 90% of players dock fleets, PvP dies (no targets). | Monitor metrics: if <10% of fleets stay deployed, increase Safe Harbor rent cost (from 1%/day to 3%/day) or add "Raid Timer" (docked fleets invulnerable for 8h, then exposed unless re-docking). |
| **PvE cannibalizes PvP** | Players farm alien hives instead of conquering. | Track playtime split: if PvE >40%, nerf PvE loot drop rates or gate best rewards behind PvP (e.g., alien queen spawns only in contested sectors). |
| **Shards fragment community** | Players on Shard A can't play with friends on Shard B. | Allow one free shard transfer per season. Add cross-shard friends list (chat, but not shared galaxy). Or: merge low-population shards after Season 1. |
| **Cosmetic-only monetization underperforms** | Revenue too low to sustain dev team. | Test "Admiral's Pass" subscription ($5/mo, all cosmetics + QoL) in Season 2. If still underperforms, consider light time-savers (e.g., "Auto-Harvest" for planets, not power boost) but NEVER sell combat power. |
| **Tech tree imbalance** | Military branch dominates (everyone specs into weapon damage). | Balance via counter-builds: Economic branch gets "Trade Embargo" ability (cut off enemy's resource income), Exploration branch gets "Sensor Jamming" (hide your fleets from enemy scans). Rock-paper-scissors. |

### 11.2 Features Deferred (Post-MVP)

- **Guild housing / monuments:** Custom alliance HQ structures (cosmetic prestige, not gameplay advantage). Deferred to Season 2.
- **Realtime skirmish mode:** 1v1 twitch duels with manual piloting (joystick controls). Deferred to Season 3 (test demand first).
- **Clan wars / territorial capture mechanics:** Formalized "control points" (alliances fight over key sectors for weekly bonuses). Deferred to Season 2.
- **Black market / smuggling economy:** Illegal goods with NPC interdiction risk. Deferred to Season 3 (complex economy tuning).
- **Player-driven NPC bounties:** Post bounties on rivals, hunters earn payout. Deferred to post-MVP (requires anti-griefing safeguards: can't bounty your own alt for infinite cash exploit).

### 11.3 Technical Unknowns (Stack Architect to Resolve)

- **Websocket scaling:** Can single server handle 1000 concurrent websockets per shard? Load test required (Week 6).
- **Database write contention:** If 500 players attack planets simultaneously, Postgres write throughput sufficient? Benchmark required.
- **Cross-shard latency:** Nexus portal battles span shards—acceptable latency if Shard A (US East) vs. Shard B (EU West)? Fallback: region-lock Nexus (US shards compete separately from EU shards).

---

## 12. Citations (Phase 1a References)

All design decisions reference **Phase 1a: Legacy System Map** (`docs/PHASE1A_LEGACY_SYSTEM_MAP.md`, PR #1). Key citations:

| Phase 1b Section | Phase 1a Source | Notes |
|------------------|-----------------|-------|
| §3.1 Core loops | Phase 1a §2.3 (player loops) | Legacy loops: exploration, trade, colony, combat (ship/planet), meta |
| §3.3 Retention hooks | Phase 1a §2.2 (tick system) | 6s ship tick, 55s planet tick (TICKTIME, PLANTIME in `GEMAIN.H:133-136`) |
| §4.1 Ship progression | Phase 1a §3.1 (WARSHP struct) | 10 ship classes, 19 phasor/shield types (`GEMAIN.H:318-385`) |
| §4.2 Planet progression | Phase 1a §3.3 (GALPLNT struct) | Environment (1-9), resource (1-9), technology (0-100%), production formula (`GEPLANET.C:195-263`) |
| §4.4 Seasons | Phase 1a §6.3 (midnight reset) | Legacy scoreboard reset (`gemidnight()` in `GEMAIN.C:1047`), replaced by seasonal leaderboards |
| §5.1 Alliances | Phase 1a §3.5 (Teams) | Legacy `teamcode`, password, shared planets (`GEMAIN.H:644-653`) |
| §5.2 Open PvP | Phase 1a §7.2 (shared world) | Legacy: no instancing, 100% shared 30×15 universe, full loot on death |
| §5.3 PvE content | Phase 1a §3.6 (Cyborgs/Droids) | Legacy NPCs (`GECYBS.C`, `GEDROIDS.C`): Cybertron AI skill 3-17, loot cap 2M |
| §6.1 Combat pacing | Phase 1a §2.2, §3.1 | 6s tick (`TICKTIME=6` in `GEMAIN.H:133`), combat resolution (`warrti()` in `GEMAIN.C:2193-2252`) |
| §6.2 Production cycles | Phase 1a §3.3 | 55s tick (`PLANTIME=55`), `multiply()` production function (`GEPLANET.C:195`) |
| §6.3 Travel time | Phase 1a §3.1 (physics) | `moveship()` in `GEFUNCS.C:603`, energy costs (ACCENGAMT=120, ROTENGUSE=30) |
| §6.4 Push notifications | Phase 1a §7.6 (breakpoints) | Legacy tick polling hostile to mobile; event-driven replacement |
| §7.1 Keep decisions | Phase 1a §8 (Keep table) | Strategic fleet/conquest, tick pacing, permadeath, sandbox PvP, production economy, fog of war, alliances |
| §7.2 Transform decisions | Phase 1a §8 (Transform table) | Text parser → visual UI, tick polling → event-driven, offline vulnerability → Safe Harbor, manual aim → auto-aim, RNG conquest → tactical layer, fixed prices → dynamic, mail → push notifications, universe size → shards, midnight reset → seasons |
| §7.3 Kill decisions | Phase 1a §8 (Kill table) | BBS session blocking, single-threaded, Btrieve, 3-letter commands, cyborg throttling, opaque spies, manual navigation |
| §8.1–8.7 (7 decisions) | Phase 1a §9 (Open questions) | Universe size (§9.1), offline protection (§9.2), combat pacing (§9.3), monetization (§9.4), PvE/PvP (§9.5), death penalty (§9.6), realtime identity (§9.7) |
| §8.2 Safe Harbor | Phase 1a §7.6 (breakpoint 2) | Legacy: offline ships vulnerable (cyborgs attack). Modern: Safe Harbor docking (NPC citadels) |
| §8.3 6s tick rationale | Phase 1a §2.2, §7.3 | Legacy: commands feel instant, world resolves at tick boundaries. Preserve strategic pacing vs. twitch |
| §8.6 Insurance | Phase 1a §3.1 (`killem()`) | Legacy: 50% cargo drop on death (`GEFUNCS.C:1058`). Modern: insurance recovers 75%, uninsured loses 50% |
| §9.1 HUD design | Phase 1a §7.6 (breakpoint 5) | Legacy: 3-letter text commands. Modern: icon-based touch UI, no text parser |
| §9.2 Deep screens | Phase 1a §3 (entities) | Map (sectors/planets), Fleet (WARSHP), Empire (GALPLNT), Social (Teams/Mail) |
| §9.3 Push notifications | Phase 1a §3.7 (Mail system) | Legacy: async text mail (`MAIL` struct, `GEMAIN.H:500-547`). Modern: in-app + push |
| §10.2 Stack handoff | Phase 1a §6 (persistence), §7.1 (concurrency) | Legacy: Btrieve, single-threaded, tick polling. Modern: PostgreSQL, microservices, event-driven |

**Legacy symbols referenced:**
- `WARSHP` (ship struct, 512B, `GEMAIN.H:318-385`)
- `WARUSR` (user account, 256B, `GEMAIN.H:292-309`)
- `GALPLNT` (planet, 512B, `GEMAIN.H:437-461`)
- `GALSECT` (sector, 512B, `GEMAIN.H:423-433`)
- `TICKTIME=6`, `PLANTIME=55` (tick rates, `GEMAIN.H:133-136`)
- `killem()` (death handler, `GEFUNCS.C:1058`)
- `multiply()` (production, `GEPLANET.C:195`)
- `warrti()` (ship tick, `GEMAIN.C:2193`)
- `gemidnight()` (midnight reset, `GEMAIN.C:1047`)
- `cyb_init()`, `cyb_lives()` (Cybertron AI, `GECYBS.C:87, 199`)

---

**End of Phase 1b Game Design.**  
**Status:** Ready for review by Empire Lead, Client UX, Stack Architect.  
**Next phase:** Client UX wireframes (Phase 1c) + Stack architecture doc (Phase 1d).
