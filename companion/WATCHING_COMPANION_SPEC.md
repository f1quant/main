# F1 Watching Companion — Living Specification

Status: Architecture boundaries selected; implementation stack pending tool audit; all archived 2026 non-practice sessions acquired and validated

This document captures the evolving specification for a new Formula 1 watching companion. It is intentionally separate from the existing race-analysis application. Decisions will be refined as discovery continues.

## Repository and Existing Implementation Context

### Repository layout

- The Git repository is `github/`, with remote `https://github.com/f1quant/main.git`.
- The active production application is `github/index.html`.
- `old/` contains predecessor pages and experiments and is not the current application.
- `text/` contains supporting write-up material.
- `fastf1_cache/` is a local FastF1 cache outside the Git repository directory.

### Current application architecture

- The production application is a static browser application with no framework, package manager, bundler, or compilation step.
- `index.html` is approximately 15,000 lines and contains most page-specific HTML, CSS, state management, calculations, and rendering logic.
- `common.js` contains CSV and IndexedDB caching, selector helpers, driver metadata, and finishing-order utilities.
- `common.css` contains the shared dark/cyan visual theme and control styles.
- Papa Parse and ECharts are vendored locally as `papaparse.min.js` and `echarts.min.js`.
- Runtime data is loaded from static files hosted with the page. Parsed CSVs are cached in browser IndexedDB.
- The current replay engine builds a session-time timeline from lap and sector timestamps, filters data according to the replay cursor, and updates subscribed panels.
- The current page includes Timing, Quali, Trace, Strategy, Fuel Effect, Tyre Deg, Pit Loss, Calculator, and Track Temp panels. Only the watching-focused behavior should inform the rebuild.

### Current preprocessing pipeline

- Python/FastF1 scripts fetch and process sessions locally.
- Generated data artifacts are committed and pushed to GitHub.
- The production page reads those static artifacts from GitHub hosting.
- `github/python utils/save_session.py` is the principal current export script.
- Race/sprint timing-feed CSVs are generated from `fastf1.api.timing_data(session.api_path)`.
- The existing export intentionally reduces FastF1 objects to lap-oriented CSV rows; the rebuild is free to define a more suitable event/telemetry representation.

### Current data files

- `all_df.csv`: race and sprint lap/weather/session rows.
- `all_df_q.csv`: qualifying lap/weather/session rows, including qualifying-segment assignment.
- `driver_info.csv`: session-aware driver number, code, team, color, full name, and headshot metadata.
- `tyre_choices.csv`: event tyre compound allocation.
- `timing_data/`: per-race and per-sprint timing feeds containing time, driver number, position, gap to leader, and interval to the car ahead.
- `strat_calc_config.json`: circuit-specific calculator defaults; likely irrelevant to the new companion.

### Local FastF1 cache

- The local `fastf1_cache/` is approximately 30 GB across roughly 417 cached sessions.
- Cached session components include car data, position data, extended timing data, timing-app data, driver information, weather, track status, session status, race-control messages, and lap counts.
- Car data accounts for roughly 12.7 GB and position data roughly 11.9 GB of the cache.
- A representative cached qualifying session has about 20 MB of car data and 19 MB of position data before any purpose-built export or web compression.
- Therefore, committing the raw FastF1 cache is not a practical delivery strategy. The new pipeline should produce compact, purpose-built replay artifacts, likely with sampling, quantization, column selection, and web compression.

## 1. Product Direction

### Confirmed

- Build a new application from scratch rather than modifying or incrementally refactoring the existing page.
- Keep the new application in the same GitHub repository as the existing project.
- Preserve the existing application unchanged.
- Focus exclusively on accompanying the viewing of Formula 1 sessions.
- Prioritize the workflows currently served by Replay Mode's Timing and Quali tabs.
- Reconsider all technical choices, including language, framework, build process, application architecture, data organization, data sources, and presentation.
- Treat support for live sessions as a major long-term goal.
- Investigate live Formula 1 data sources and parsers instead of relying exclusively on FastF1's delayed post-session data.
- Make replay support the first useful release.
- The first release may use any data available through FastF1; it is not limited to the CSV fields or files used by the existing application.
- Cache downloaded or processed FastF1 data so that sessions do not need to be fetched and transformed repeatedly.
- Optimize primarily for a laptop used as a second screen while the broadcast plays on a television.
- Provide a mobile-friendly responsive experience as a secondary target.
- Treat this primarily as a personal tool rather than designing initially for a public audience.

### Current product framing

The companion should help a viewer understand what is happening during a Formula 1 session without becoming a general-purpose historical analysis tool or tyre-strategy calculator. It should work especially well as a laptop-based second screen alongside a race broadcast, making timing, gaps, lap progress, tyre information, and qualifying progression easier to follow. A responsive mobile layout should retain the essential experience on a smaller display.

## 2. Initial Scope

The first useful release is replay-first and may be based on cached FastF1 data. Candidate session types are:

- Replay companion for completed sessions
- Race timing
- Sprint timing
- Qualifying and sprint-qualifying timing

Practice sessions are out of scope for v1.

Live session support is a later goal. The initial architecture should avoid making it unnecessarily difficult, but the first release does not depend on solving live ingestion.

Historical analysis, strategy optimization, fuel-effect regression, tyre-degradation regression, and similar research workflows are presumed out of scope unless later identified as essential to watching.

## 3. Core Experience

### Known priorities

- Race viewing companion
- Qualifying viewing companion
- Timing information synchronized to session progress
- A purpose-built interface rather than a collection of analysis tabs
- Laptop second-screen use, with mobile-friendly responsive behavior

### Race and sprint workflow

The primary race/sprint view should be anchored by a conventional full-field driver classification display. Its essential information includes:

- Current position/classification
- Driver identity
- Latest lap time
- Gap to the leader
- Interval to the car ahead
- Sector times
- Current tyre compound and tyre age
- Personal-best and session-best color semantics
- Pit and out-lap status
- Track status

The timing tower should remain visible throughout the main viewing experience. Its column set may adapt to the available width and the active secondary view; not every column must remain visible simultaneously.

Predicted position after a pit stop is desirable in the longer term, but is predictive analytics and is explicitly deferred beyond v1.

The next most important view is a lap-time plot. The viewer typically:

- Selects the leading drivers plus several other drivers of interest.
- Automatically excludes slow or non-representative laps, including pit laps, safety-car laps, and related exceptional laps, so that the useful pace variation is not visually compressed.
- Can manually restore automatically excluded laps when needed.

A race trace is a secondary view used less frequently to understand whether the gap between particular drivers is growing or shrinking.

### Qualifying workflow

The principal value of the qualifying view is whole-field awareness. Unlike the television broadcast, it should show every driver who is preparing for or completing a lap, together with their sector performance.

The current application is useful but has two notable weaknesses that the rebuild should solve:

- It does not clearly represent drivers before they begin a hot lap.
- A lap that is aborted or later deleted/disqualified may never be represented as a hot lap. The existing workaround avoids leaving an aborted lap ticking forever, but loses useful information about what the driver was attempting at the time.

The new state model should distinguish an attempted hot lap from its eventual outcome. It should allow a lap to progress live/replay as an attempt, then resolve it as completed, aborted, invalidated, or otherwise ended without leaving stale timers running.

Qualifying is not a single linear sequence. A driver may complete multiple preparation laps before a hot lap, or run a hot lap, a cooldown lap, and another hot lap without returning to the pits. The state model must therefore support repeated and looping transitions among out/preparation, hot, cooldown, and pit states.

More granular progress than three sectors is a high-value opportunity. A continuously updating delta is the preferred presentation, subject to what FastF1 telemetry can reliably support. Mini-sectors or track-position context may supplement it later.

The preferred continuous-delta reference is the current provisional pole time for that qualifying segment. Before any driver has set a time in the active segment, the best time from the preceding segment should be used as the initial reference.

### Questions to resolve

- Primary device and viewing environment
- Whether the app is a second-screen dashboard or can share a screen with the broadcast
- Desired level of interaction versus passive monitoring
- Which information must be visible simultaneously
- Whether spoilers must be prevented by default
- How live, delayed-live, and historical replay modes should differ
- Exact responsive compromises for the mobile layout
- Exact classification columns and behavior
- How adaptive timing-tower columns are prioritized at different widths
- How qualifying preparation, hot, cooldown, aborted, and invalidated states are inferred from recorded data
- The reference lap and presentation for continuous qualifying delta

## 4. Data

### Existing local data

The current application has reusable historical data and parsing knowledge:

- Race and sprint lap data in `all_df.csv`
- Qualifying data in `all_df_q.csv`
- Driver/team metadata in `driver_info.csv`
- Per-session timing feeds in `timing_data/`
- FastF1-derived fields for lap times, sector times, compounds, tyre life, track status, weather, position, and related metadata

The new application's canonical data model and storage format are undecided. Existing CSV files may be used for migration or validation without becoming the permanent runtime format.

For the first release, the data boundary may include any information FastF1 exposes, not only the fields currently exported to CSV. Replay sessions should be fully acquired, processed, and cached ahead of playback so the replay UI does not depend on incremental FastF1 requests. The equivalent live-data pipeline remains undecided.

### Live-data goal

The desired future state is to ingest session data while an event is taking place. Discovery must cover:

- Available Formula 1 live timing endpoints and protocols
- Authentication, access restrictions, reliability, and terms-of-use implications
- Incremental event ingestion and reconnect behavior
- Normalization of live and historical data into one model
- Recording a live session so it can later be replayed identically
- Fallback behavior when live timing is unavailable or incomplete

No live-data source has been selected yet.

## 5. Architecture

The replay-v1 architecture was selected after the feasibility work recorded in Sections 10–12. The confirmed boundaries are: a static browser application, an offline artifact builder, a versioned normalized event contract shared by replay and live sources, and a local collector service for the first live version. React/TypeScript/Vite for the browser and Python/FastF1 for acquisition and validation remain leading candidates, but the exact implementation stack is provisional until the installed local toolchain can be inventoried with working shell access. Replay remains deployable as a static application; live mode must not depend on a browser connecting directly to Formula 1 or holding source credentials.

The architecture should be evaluated against these likely needs:

- A responsive, information-dense UI with frequent incremental updates
- Deterministic replay of recorded session events
- Local or server-side live-data ingestion
- Efficient storage and querying of session timelines
- Cached retrieval and preprocessing of FastF1 sessions
- A normalized replay artifact containing everything needed during playback
- Isolation from the existing application
- Straightforward deployment within or alongside the current GitHub-hosted project
- Maintainability as additional timing views are introduced

Because this is initially a personal tool, the selected architecture favors simplicity and local control over multi-user scale while keeping a clean boundary between ingestion, normalized session data, and presentation. The existing local-to-GitHub artifact workflow remains the replay delivery path. Live adds a local collector without changing the UI contract. Hosted live access, including a possible Cloudflare Containers/Workers/R2 deployment, is explicitly deferred until local live mode works.

### Feasibility gates

The two required investigations are complete:

1. **Live timing feasibility:** Determine whether Formula 1 timing data can be accessed during a session with sufficient fields, latency, stability, and acceptable operational constraints.
2. **Continuous qualifying delta feasibility:** Determine whether FastF1 replay data—and eventually the live feed—contains synchronized position or telemetry samples that can support a reliable whole-field delta more granular than sectors.

Sections 10 and 11 separately document what is technically possible, what is reliable enough to design around, and what remains experimental.

### Local feasibility evidence already found

The repository contains useful prior experiments, but they are not substitutes for current external documentation or a real live-session test:

- `github/python utils/temp.py` constructs a Formula 1 endpoint at `https://livetiming.formula1.com{api_path}CarData.z.jsonStream`, downloads the stream, and decodes timestamp-prefixed Base64/zlib payloads. This demonstrates direct parsing of archived Formula 1 car-data stream payloads. It does **not** by itself prove that an unauthenticated live connection is currently available, stable, or suitable for production.
- FastF1 cache entries show that car telemetry and position samples are available for historical sessions, together with timing, status, weather, and race-control data.
- `github/python utils/q3_animation.py` already compares qualifying laps using `lap.get_pos_data()` and `lap.get_car_data()`, interpolates driver positions, and computes a continuously varying delta against a reference lap.
- `github/python utils/track_line3.py` and `pos_data_analysis.py` experiment with fitting a circuit centerline and projecting noisy FastF1 position samples onto it.

These experiments provide strong evidence that a continuous delta for **completed replay laps** is technically achievable. The research resolved the sample-rate and live-availability questions. Projection error, start/finish handling, invalid/incomplete laps, artifact size, and live latency remain implementation or live-test validation items.

### External research

Current 2026 documentation and source code were inspected. Findings are in Sections 10 and 11, and direct links are collected in Section 13.

## 6. Modes and Time Semantics

The application may need to distinguish:

- **Live:** follows incoming timing data in real time.
- **Delayed live:** follows the live event with a user-selected delay to match a broadcast.
- **Replay:** plays a recorded session from any point at adjustable speed.
- **Final:** shows the complete session without progressive reveal.

Replay must support pausing, rewinding, and seeking. The existing replay controls are considered a good starting point. Additional controls such as variable playback speed, keyboard shortcuts, event stepping, and event markers are not required for v1. Less-manual synchronization with a television broadcast is desirable, but no feasible mechanism has yet been identified. Live, delayed-live, and final modes remain candidate future concepts.

## 7. Design Principles

Candidate principles to validate during discovery:

- Optimize for comprehension during a session, not post-session analysis.
- Keep the most important state visible without tab switching.
- Make position changes, pit events, lap completion, sector performance, and session status immediately legible.
- Avoid revealing future information while replaying a session.
- Make live and replay experiences use the same underlying interface and event model where practical.
- Degrade gracefully when data fields arrive late or are missing.
- Preserve attempted-lap history even when a lap is later aborted or invalidated.
- Show meaningful whole-field activity rather than only the few drivers emphasized by the broadcast.
- Prevent exceptional slow laps from compressing the useful range of pace charts.
- Keep the timing tower visible while allowing its columns to adapt to space and context.
- Make automatic data filtering transparent and reversible.

## 8. Out of Scope

Provisionally out of scope:

- Modifying the existing application
- Optimal tyre-strategy simulation
- Fuel-effect analysis
- Tyre-degradation regression tools
- General-purpose historical race research

This list will change if discovery identifies watching-critical features.

## 9. Open Questions and Decision Log

### Discovery round 1 — answered

1. First release: replay support using cached FastF1 data, without restricting the rebuild to existing project exports.
2. Primary environment: broadcast on a television and companion on a laptop; mobile-friendly behavior is also desired.
3. Race priorities: classification/timing tower, filtered selectable-driver lap-time plot, then race trace.
4. Qualifying priorities: whole-field hot-lap awareness, better pre-lap states, correct treatment of aborted/deleted laps, and potentially mini-sector detail.
5. Replay must support pause and rewind; less-manual television synchronization would be valuable if feasible.
6. Audience: primarily personal use.

### Discovery round 2

1. Replay sessions will be fully acquired, processed, and cached; live acquisition remains undecided.
2. The timing tower should remain visible, with an adaptive set of columns.
3. Required timing information includes both gap types, tyre age, performance coloring, pit/out-lap state, and track status. Position gained/lost is unnecessary. Pit prediction is deferred beyond v1.
4. Exceptional laps should be hidden automatically but manually restorable.
5. Qualifying transitions must loop to support multiple preparation laps and hot-cooldown-hot sequences.
6. Continuous delta is the preferred form of sub-sector qualifying detail.

### Discovery round 3

1. V1 covers races, sprints, qualifying, and sprint qualifying; practice is excluded.
2. The current Python-to-GitHub artifact pipeline may remain, but the final delivery model depends on live feasibility.
3. Basic play, pause, seek, and rewind controls are sufficient for v1.
4. The proposed race and qualifying timing-tower contents are accepted as a starting point.
5. Continuous qualifying delta should target provisional pole, falling back to the prior qualifying segment before the first representative time.
6. Track map and team radio are desired additional data types.

### Remaining validation

- Benchmark the purpose-built artifact and centerline projection on representative qualifying and race sessions.
- Test paid OpenF1 during a real qualifying session and race for latency, completeness, revisions, and reconnect behavior.
- Validate the attempted-lap phase heuristic without future information.
- Decide whether OpenF1's cost and terms are acceptable before selecting it as the live provider.

### Decision log

| Date | Decision | Status |
| --- | --- | --- |
| 2026-08-18 | Create a new watching-focused application alongside the existing app. | Confirmed |
| 2026-08-18 | Preserve the existing application unchanged. | Confirmed |
| 2026-08-18 | Keep both applications in the same GitHub repository. | Confirmed |
| 2026-08-18 | Treat live-session support as a major product goal. | Confirmed |
| 2026-08-18 | Make cached FastF1 replay the first useful release. | Confirmed |
| 2026-08-18 | Optimize for laptop second-screen use and support mobile responsively. | Confirmed |
| 2026-08-18 | Make a full-field classification display the primary race/sprint view. | Confirmed |
| 2026-08-18 | Make selected-driver, slow-lap-filtered lap-time plotting the secondary race view. | Confirmed |
| 2026-08-18 | Preserve attempted qualifying laps independently of their eventual outcome. | Confirmed |
| 2026-08-18 | Design initially as a personal tool. | Confirmed |
| 2026-08-18 | Fully process and cache each replay session before playback. | Confirmed |
| 2026-08-18 | Keep an adaptive timing tower visible throughout the primary experience. | Confirmed |
| 2026-08-18 | Automatically hide exceptional laps while allowing manual restoration. | Confirmed |
| 2026-08-18 | Support looping qualifying lap states rather than a rigid lifecycle. | Confirmed |
| 2026-08-18 | Prioritize continuous qualifying delta as the finer-grained performance view. | Confirmed |
| 2026-08-18 | Defer predicted post-pit position and predictive analytics beyond v1. | Confirmed |
| 2026-08-18 | Include race, sprint, qualifying, and sprint qualifying in v1; exclude practice. | Confirmed |
| 2026-08-18 | Keep v1 replay controls to play, pause, seek, and rewind. | Confirmed |
| 2026-08-18 | Use provisional pole as the default continuous-delta reference, with prior-segment fallback. | Confirmed |
| 2026-08-18 | Add track map and team radio to the desired watching data. | Confirmed |
| 2026-08-18 | Require cached and live sources to present a common normalized interface to the UI. | Confirmed |

## 10. Feasibility Report — Live Timing

Research completed 2026-08-18. Native web access worked. The two requested shell checks did not: both `https://example.com/` and the FastF1 documentation URL failed with exactly `curl: (6) Could not resolve host`. External conclusions below therefore use the native web reader and linked current sources, not shell HTTP responses.

### Direct Formula 1 feed

#### Technically possible

The current FastF1 client is implementation evidence for this connection sequence:

1. Send `OPTIONS` to `https://livetiming.formula1.com/signalrcore/negotiate` and retain the returned `AWSALBCORS` cookie.
2. Obtain a Formula 1 subscription JWT through FastF1's browser-assisted Formula1/F1TV login flow.
3. Connect to `wss://livetiming.formula1.com/signalrcore` using SignalR Core and the JWT.
4. Register for the `feed` callback and invoke `Subscribe` with the desired topic list.
5. Persist the subscription result and subsequent incremental messages with their source timestamps.

The current topic list is `Heartbeat`, `AudioStreams`, `DriverList`, `ExtrapolatedClock`, `RaceControlMessages`, `SessionInfo`, `SessionStatus`, `TeamRadio`, `TimingAppData`, `TimingStats`, `TrackStatus`, `WeatherData`, `Position.z`, `CarData.z`, `ContentStreams`, `SessionData`, `TimingData`, `TopThree`, `RcmSeries`, and `LapCount`.

The watching-critical content is present:

- `TimingData`: position/classification, gaps and intervals, lap count, lap and sector timing, speed traps, and pit transitions. It is a sparse change stream, not a complete row on every message.
- `TimingAppData`: stint, tyre, and timing-app state.
- `Position.z`: timestamped X/Y/Z position and on/off-track state.
- `CarData.z`: speed, RPM, gear, throttle, brake, and DRS.
- `TrackStatus`, `SessionStatus`, `ExtrapolatedClock`, `LapCount`, `RaceControlMessages`, and `WeatherData`: session context.
- `DriverList`: driver/team identity metadata.
- `TeamRadio`: transmission metadata. The audio itself is referenced by a recording URL rather than embedded in the event.

FastF1 documents position samples at usually about 220 ms and car samples at usually about 240 ms—roughly 4.5 Hz and 4.2 Hz. The two streams have different timestamps and must be aligned or interpolated. Timing and classification fields are event-driven; no current official latency or update-frequency guarantee was found. Weather is approximately once per minute.

FastF1's supported `SignalRClient` intentionally writes the feed for later loading and states that it cannot be used for supported real-time analysis. That is a limitation of the provided client/API, not proof that messages arrive only after the lap: its callback receives and writes live `Position.z`, `CarData.z`, and timing messages as they are pushed. A custom collector can process the callback in real time while also writing the raw recording.

#### Not reliable enough to make the production dependency

- FastF1 3.7 changed to SignalR Core after Formula 1 phased out the older endpoint. FastF1 says authenticated use now requires an active F1TV Access/Pro/Premium subscription; unauthenticated access may be empty or partial.
- There is no official public schema, compatibility promise, latency SLA, or documented recovery protocol. The transport and fields can change without notice.
- FastF1's current client contains a `TODO` for automatic reconnect. Its documented recovery is a manual restart in append mode. `LiveTimingData` can combine overlapping files and remove duplicates afterward, but this does not prove that messages missed while disconnected can be recovered live.
- The `Subscribe` completion result is treated by the FastF1 code as per-topic current data, which is useful as a re-baseline snapshot. This is implementation evidence, not a documented guarantee. A reconnect must re-subscribe, accept a new snapshot, mark the gap, and avoid pretending that lost high-frequency samples were recovered.
- A live-session soak test is still required. No authenticated real-session connection was attempted in this research pass.

#### Browser and terms constraints

A static browser client is not an acceptable direct-F1 design. FastF1's authentication flow obtains and stores a subscription JWT locally, its client needs a negotiated load-balancer cookie and custom SignalR authorization, and a browser application would expose credentials/tokens and depend on unverified cross-origin behavior. A local or hosted collector is required if this feed is ever tested.

More importantly, Formula 1's F1TV subscription terms, last updated August 2025, restrict timing/API data to private viewing through the supplied platform, prohibit tampering with or using that data for another purpose, prohibit copying/recording/storing most service content, and prohibit text/data mining and web scraping. This creates a material contractual risk even for a personal application. This is an operational conclusion, not legal advice: direct Formula 1 ingestion must remain an opt-in experiment and must not be the default or required live source without permission or a better rights basis.

### OpenF1 alternative

OpenF1 is an unofficial but documented intermediary and is the preferred first live-adapter candidate if its subscription cost and terms are acceptable:

- Historical data from 2023 onward is free; real-time data requires a paid account.
- OAuth2 access tokens are obtained by exchanging account credentials and expire after one hour.
- Live push is available through MQTT over TLS or MQTT over WebSocket at `wss://mqtt.openf1.org:8084/mqtt`.
- Topics mirror REST resources such as `v1/laps`, `v1/location`, `v1/car_data`, `v1/position`, `v1/intervals`, `v1/stints`, `v1/race_control`, and `v1/team_radio`.
- Each pushed document includes an ever-increasing `_id`; `_key` identifies revisions of the same logical object. That is a better basis for ordering and upserting late lap/sector revisions than the undocumented direct feed.
- Location and car data are documented at about 3.7 Hz. Position, interval, and gap products are advertised at about four-second updates. Qualifying lap data includes mini-sector status arrays, though OpenF1 warns that their colors do not always match television timing exactly.
- OpenF1 recommends MQTT/WebSocket rather than polling for live use. It also explicitly requires credential exchange in a backend and recommends backend-held live connections when token exposure matters.

OpenF1 does not remove all operational uncertainty: it has no documented end-to-end latency SLA or documented guarantee of retained MQTT messages, and it ultimately depends on an upstream Formula 1 feed. Use REST for an initial snapshot and bounded backfill, then MQTT from a stored `_id` high-water mark; expose missing intervals to the UI rather than silently interpolating them. A real qualifying and race test must measure latency, revisions, disconnect recovery, and completeness before live mode is promoted.

Team radio is desirable but non-critical. Both sources expose metadata/URLs for only the transmissions Formula 1 publishes. OpenF1 currently warns that coverage decreased sharply in 2026 and that most events provide none. The UI must treat radio as an optional capability, never as a session invariant, and replay artifacts should store metadata but not bundle audio.

### Live feasibility verdict

| Question | Conclusion |
| --- | --- |
| Is whole-field live timing technically obtainable? | Yes, through authenticated direct SignalR or paid OpenF1. |
| Is direct Formula 1 ingestion reliable and acceptable enough to design around? | No. It is undocumented, mutable, subscription-gated, and has serious terms risk. |
| Is OpenF1 suitable for the first adapter? | Plausibly yes, but only after a paid real-session test and terms/cost acceptance. |
| Can a static GitHub Pages client safely own live ingestion? | No. Replay can remain static; live needs a credential-holding collector. |
| Are reconnect and missed-message semantics solved? | No. The architecture can handle gaps and snapshots, but source behavior still needs live validation. |

## 11. Feasibility Report — Continuous Qualifying Delta

### Historical replay

Continuous delta for completed and progressively replayed qualifying laps is feasible.

- FastF1 provides original car and position samples from 2018 onward. Position is usually sampled every 220 ms and car telemetry every 240 ms.
- FastF1 warns that position is approximate, the car and position clocks do not align, and merged telemetry contains interpolated values. Original streams should therefore be preserved separately during preprocessing.
- The local experiments already prove the main operations: `q3_animation.py` compares lap paths continuously; `track_line3.py` smooths multiple laps, fits a closed centerline, and projects samples; `pos_data_analysis.py` explores position/car clock alignment and speed consistency.
- The local 2026 Hungarian qualifying cache contains about 36 MB of processed position data and 21 MB of processed car data, confirming that browser delivery needs a purpose-built representation rather than cached FastF1 objects.

The artifact builder may use full-session information to construct circuit geometry, because geometry does not reveal a performance outcome. It must not reveal performance-derived state early. Every timing change, attempt outcome, reference-lap change, deletion, and telemetry sample needs an `availableAtSessionMs`; replay reducers may consume it only when the cursor reaches that timestamp. FastF1's finalized lap table alone is insufficient for spoiler-safe replay because it includes corrections and outcomes learned later.

### Live active laps

The underlying streams contain position and car samples during the active lap, so a custom collector can calculate a provisional delta before the lap finishes. OpenF1 also pushes live location documents. FastF1's inability to analyze its recording through the standard API until afterward does not make active-lap delta impossible.

What remains experimental is quality, not basic availability:

- source-to-screen delay under live load;
- GPS jitter, temporary zero/stale coordinates, and ambiguous nearby track segments;
- synchronization of position samples with start/finish and segment changes;
- whether reconnect/backfill is fast enough to resume a meaningful delta;
- how quickly a push lap can be distinguished from a preparation or cooldown lap without future knowledge.

### Distance and delta method

1. Build a smooth closed centerline from several clean completed laps, resampled by arc length. Preserve the start/finish anchor and pit-lane geometry separately.
2. Project each position sample onto a dense centerline index. Use a continuity-constrained map matcher—not independent nearest points—so progress normally moves forward and does not jump across nearby sections, overpasses, or the start/finish wrap.
3. Use original sample timestamps. Use car speed only to reject or repair implausible position jumps; do not merge all channels onto an invented high-frequency clock.
4. Quantize the resulting lap progress to an unsigned 16-bit value over `[0, 1)`. Store projection error and validity flags so the UI can hide low-confidence delta values.
5. For each valid reference lap, construct a monotonic lookup `referenceElapsedMs(progress)` from its observed samples.
6. For an active attempt, calculate `activeElapsedMs - referenceElapsedMs(progress)`. Smooth only the display value with a short causal filter; preserve the unsmoothed value for testing.
7. The active segment's current valid provisional pole is the reference. Before that segment has a valid time, use the preceding segment's best valid lap. If a reference lap is later deleted, emit a timestamped reference-revocation event and fall back to the next valid lap.

Do not show a numeric delta in the pit lane, while projection confidence is low, before a valid reference exists, or after an attempt has ended. Mini-sector colors can remain a fallback when continuous position data is missing.

### Attempt state and outcomes

An `Attempt` is a first-class entity separate from a finalized FastF1 `Lap`. It has timestamped phase revisions and a separately resolved outcome:

- Phase: `pit`, `out`, `preparation`, `push-likely`, `cooldown`, or `unknown-on-track`.
- Outcome: `open`, `completed`, `aborted`, `invalidated`, or `incomplete`.

Crossing the start/finish line opens a new attempt unless the car is in the pit-lane path. Pit transitions, segment updates, speed/progress patterns, and the previous attempt inform a phase with a confidence value. Because intent is not directly transmitted, preparation versus cooldown versus push is an inference; the UI must prefer `unknown-on-track` or `push likely` over false certainty.

A received lap time completes an attempt. A pit entry or session stop can close an unfinished attempt as incomplete/aborted. Race-control deletion messages revise a completed attempt to invalidated and preserve the recorded time and reason. A missing official lap time must not make the attempt disappear. FastF1's final `Deleted` and `DeletedReason` fields are useful for validation, while replay resolution must occur at the original message time.

### Compact representation and size estimate

Use two artifact layers:

- A small, schema-versioned event stream for timing/classification, stint/tyre changes, flags, messages, lap-attempt revisions, radio metadata, and reference changes.
- Per-driver binary sample blocks for `deltaTimeMs`, quantized X/Y, normalized progress, projection quality, and flags. Keep car channels in an optional block; continuous delta and the track map do not require RPM/throttle/gear in v1.

At 4.5 Hz for 20 drivers, a 90-minute qualifying session has roughly 486,000 position samples and a two-hour race roughly 648,000. At about 9 bytes per core sample, that is roughly 4.4 MB and 5.8 MB before web compression. A practical target is 2–6 MB compressed per session for the core event plus position artifact, excluding audio; optional car telemetry may add several megabytes. These are engineering estimates, not measured exporter results. The first exporter milestone must benchmark at least one qualifying and one race before repository-wide retention is decided.

### Delta feasibility verdict

| Capability | Status |
| --- | --- |
| Completed historical lap versus completed reference | Reliable enough for v1 after projection-quality tests. |
| Spoiler-safe progressive replay delta | Feasible with timestamped raw-derived events; do not drive it from finalized lap rows alone. |
| Live active-lap delta | Technically feasible, experimental until a real-session validation. |
| Exact push/prep/cooldown intent | Not directly available; expose an inference and confidence. |
| Deleted/aborted attempt preservation | Feasible with first-class attempts and timestamped outcome revisions. |

## 12. Architecture Decision

### Confirmed shape and provisional implementation candidates

- Create an isolated `companion/` directory in the Git repository. Keep the existing root application and assets unchanged.
- Keep React + TypeScript + Vite as the leading UI candidate, with ECharts for plots, Canvas for the frequently updated track map, and ordinary accessible DOM for the timing tower. Confirm or replace these choices only after auditing usable installed tools and credible alternatives.
- Put the normalized model and schema definitions in `companion/schema/`; the exact schema/type-generation packages depend on the confirmed stack.
- Put acquisition and processing in `companion/pipeline/`. Python and FastF1 remain the leading acquisition/validation candidates, not yet a final toolchain commitment.
- Preserve downloaded source messages byte-for-byte under `companion/raw/` locally. Raw `*.jsonStream` payloads and session `Index.json` files are ignored by Git; documentation remains versioned.
- Put the browser application in `companion/app/`. A limited v1 processed session set may live under its public data directory for GitHub Pages. Do not commit team-radio audio.

### Common source contract

The UI consumes only normalized envelopes, regardless of source:

```text
Envelope {
  schemaVersion, sessionId, source,
  sequence, availableAtSessionMs,
  observedAtUtc, type, entityId, revision, payload
}
```

The core reducer must be deterministic: the same ordered envelopes produce the same visible state. `ReplaySource` reads artifacts and releases envelopes according to the replay cursor. `LiveSource` receives the same envelopes from a collector. Periodic reducer checkpoints—approximately every 30 seconds plus qualifying-segment boundaries—make seeking fast without changing semantics.

The model should preserve raw-source identity and revision information. Late corrections are new envelopes, not mutation of history. Missing source intervals are explicit health events. Source-specific data that cannot be normalized without loss can be retained in an optional extension payload but must not leak into UI components directly.

### Replay deployment

Replay is a static GitHub Pages application. The build fetches a small session manifest, then only the event and sample blocks needed for the chosen session/view. Browser IndexedDB caches immutable artifacts by content hash. Service-worker/offline support can be added after the first vertical slice; it is not an initial dependency.

The browser must not load the raw Formula 1 topic streams. The offline pipeline causally normalizes them ahead of time, preserving original availability times and revisions, then packages compact immutable event, sample, index, and checkpoint artifacts. Dynamic browser loading applies to those processed artifacts. Raw streams remain local pipeline inputs and debugging evidence.

### Live deployment

The first live version is local-server-only. Its credential-holding collector also serves the built UI and a same-origin WebSocket endpoint on localhost; this avoids putting secrets in GitHub Pages and avoids HTTPS-page-to-local-insecure-WebSocket problems. Remote mobile access is out of scope for this phase.

The collector writes an append-only local raw recording before normalization. Archived replay and live capture must feed the same causal, incremental processor; they differ only in whether messages arrive from saved streams or the network. FastF1 and OpenF1 are implementation references and optional validation tools, not the canonical processing pipeline. A later source adapter can add authentication, reconnect/backfill, and explicit health/gap events.

A hosted collector is a later deployment phase. Cloudflare Containers plus a Worker and private R2 storage is the leading candidate discussed so far, but it is not selected or required now. If adopted, raw live recordings would be written to private object storage; only processed replay artifacts would be publicly served. Until then, raw archives stay on the local computer and should be backed up privately rather than committed to Git.

### Why this architecture

- Replay ships without a server and preserves the current GitHub-hosted workflow.
- A raw-message-first processor keeps replay behavior aligned with live behavior and avoids depending on finalized, post-session FastF1 objects.
- The event contract prevents the replay UI and future live UI from becoming separate products.
- A collector isolates credentials, unstable transports, reconnect logic, and recording from presentation.
- Timestamped revisions preserve aborted/deleted attempts and prevent replay spoilers.

### First implementation sequence

1. Restore shell access to the user's installed development tools and inventory viable existing stacks before installing anything.
2. Confirm the UI, pipeline, local-server, package-management, test, and deployment toolchain.
3. Create the deterministic timestamp merge/replay reader from the acquired raw fixtures.
4. Define schema v1 and reducer fixtures for a race classification update, tyre/pit changes, a qualifying attempt, deletion, and reference replacement.
5. Feed both archived replay and future live capture through the same incremental processor.
6. Build replay and local live modes against the same normalized contract, then run a live-session soak test before treating live mode as reliable.

## 13. Verified Source Register

- [FastF1 live timing guide](https://theoehrly-fast-f1.mintlify.app/guides/live-timing)
- [FastF1 live timing API reference](https://theoehrly-fast-f1.mintlify.app/api/livetiming)
- [Current FastF1 SignalR client source](https://github.com/theOehrly/Fast-F1/blob/main/fastf1/livetiming/client.py)
- [Current FastF1 F1TV authentication source](https://github.com/theOehrly/Fast-F1/blob/main/fastf1/internals/f1auth.py)
- [FastF1 3.7 release notes for SignalR Core and authentication](https://github.com/theOehrly/Fast-F1/releases/tag/v3.7.0)
- [FastF1 telemetry reference](https://docs.fastf1.dev/api_reference/telemetry.html)
- [FastF1 raw API reference, including sample rates](https://docs.fastf1.dev/api.html)
- [FastF1 accuracy guidance](https://docs.fastf1.dev/howto_accurate_calculations.html)
- [FastF1 lap fields, including deletion metadata](https://docs.fastf1.dev/core.html)
- [OpenF1 endpoint documentation](https://openf1.org/docs/)
- [OpenF1 authentication and MQTT/WebSocket guide](https://openf1.org/auth.html)
- [OpenF1 source repository](https://github.com/br-g/openf1)
- [Formula 1 F1TV subscription terms](https://www.formula1.com/en/information/f1-tv-subscription-terms.384sQqjslhQ2Rhm1LdKgfD)

## 14. Decision Log Additions

| Date | Decision | Status |
| --- | --- | --- |
| 2026-08-18 | Use a static replay application plus an optional separate live collector. | Confirmed |
| 2026-08-18 | Use React, TypeScript, and Vite for the new UI; retain Python/FastF1 for acquisition and preprocessing. | Provisional pending installed-tool audit |
| 2026-08-18 | Make a versioned, timestamped, revision-aware event envelope the only UI data boundary. | Confirmed |
| 2026-08-18 | Preserve source recordings and explicitly represent gaps, corrections, and attempt outcomes. | Confirmed |
| 2026-08-18 | Treat historical continuous qualifying delta as feasible for v1, subject to projection-quality fixtures. | Confirmed |
| 2026-08-18 | Keep live continuous delta experimental until a real qualifying/race soak test. | Confirmed |
| 2026-08-18 | Do not make direct Formula 1 ingestion the default live source because of undocumented behavior and terms risk. | Confirmed |
| 2026-08-18 | Evaluate paid OpenF1 as the first live adapter using REST snapshot/backfill plus MQTT push. | Provisional |
| 2026-08-18 | Treat team radio as optional and store metadata/URLs only. | Confirmed |
| 2026-08-18 | Build one causal, incremental processor over raw Formula 1 messages for both archived replay and live capture; use FastF1 and OpenF1 as references and validators rather than the canonical pipeline. | Confirmed |
| 2026-08-18 | Dynamically load compact preprocessed replay artifacts in the browser; never make raw topic streams browser runtime inputs. | Confirmed |
| 2026-08-18 | Keep raw `*.jsonStream` and session `Index.json` files local and ignored by Git for now; publish only processed replay artifacts. | Confirmed |
| 2026-08-18 | Make the first live implementation a local server that also serves the UI and same-origin WebSocket. | Confirmed |
| 2026-08-18 | Defer hosted/mobile live deployment; Cloudflare Containers/Workers with private R2 is a later candidate, not a current dependency. | Confirmed |
| 2026-08-18 | Audit accessible installed tools and alternatives before confirming or installing the implementation stack. | Confirmed |

## 15. New-Chat Handoff

### Current objective

Fix Codex shell access to the user's existing development toolchain, then start a new Codex session and inventory what is already installed and viable. Do not install packages or scaffold the processing pipeline/UI until that audit is complete and the stack has been confirmed.

### First checks in the new session

The current sandbox can access the workspace but cannot execute the user's Python under `~/.pyenv`; it returns `Operation not permitted`. `node --version` reports v24.11.1 through the execution environment, while npm, Homebrew, Docker, and Wrangler are not currently executable. `/usr/bin/python3` and `/usr/bin/git` fall through to Apple Command Line Tools stubs. These observations prove an access/PATH problem, not that the applications are absent from the computer.

After permissions are repaired, inspect the real paths and versions for Python/pyenv, Node/npm and alternative JavaScript runtimes/package managers, Git, Docker or alternative container tools, Wrangler, and available test/build tools. Also inspect installed Python and JavaScript packages. Prefer a suitable existing toolchain; do not install or replace anything without first reporting the audit.

### Data and architecture decisions

- Build our own raw-message processing pipeline.
- Archived streams and live messages must enter the same ordered, causal reducer.
- Replay browsers load preprocessed artifacts, not raw source streams.
- Raw `*.jsonStream` and session `Index.json` files stay local and are ignored by Git for now.
- Implement live mode with a local server first; defer Cloudflare or other hosted deployment.
- Treat React/TypeScript/Vite and Python/FastF1 as candidates pending the installed-tool audit.
- Use FastF1 and OpenF1 source code to learn message semantics and validate results; do not make FastF1's finalized `Session.load()` output the pipeline's source of truth.
- Do not self-host OpenF1's MongoDB/API/MQTT stack for this personal project unless a later need justifies it.
- Do not start processor or UI implementation until the stack is confirmed.

### Immediate completion criteria

1. Existing development applications and packages are visible and executable from the new Codex session.
2. Viable installed alternatives are compared before any new installation.
3. The selected stack and exact versions are recorded here.
4. Only then does implementation begin with the deterministic raw reader.

### Acquisition result — 2026-08-18

Complete. Shell access to the Codex skill directory and shell HTTP access to the official archive both succeeded. `companion/raw/2026-hungary-race/` now contains `Index.json` plus all 33 unique `StreamPath` files referenced by its `Feeds` object, with no missing or extra files. The fixture is 30,611,647 bytes in total and contains 203,569 timestamped stream records. Every stream's local byte count and MD5 digest match the official response's `Content-Length` and S3 `ETag`.

The raw formats are consistent across the fixture:

- `Index.json` and every stream begin with a UTF-8 BOM.
- Every stream uses CRLF-delimited records, including a final CRLF.
- Each record begins with a 12-byte `HH:MM:SS.mmm` session-time prefix followed immediately by one JSON value. Timestamps are nondecreasing within every feed.
- Ordinary feeds contain a JSON object after the timestamp.
- `CarData.z.jsonStream` and `Position.z.jsonStream` instead contain a JSON string holding strict Base64. Every one of their 18,686 frames decodes as raw DEFLATE and then parses as a JSON object. Their first decoded shapes are `Entries` and `Position`, respectively.
- Representative bounded prefixes were inspected for the index, session information, timing data, race-control messages, car data, and position data. The stream time range extends through approximately `02:37:08`.
- The index's `KeyFramePath` references are snapshots, not timestamped streams. They were not downloaded as part of the requested `StreamPath` fixture and must remain separate from causal replay input if acquired later.

The next implementation step is a deterministic raw reader, not UI work: remove the BOM once per file; iterate CRLF records without rewriting the source; split the fixed-width timestamp from the JSON value; decode `.z` values through JSON string -> Base64 -> raw DEFLATE -> JSON; and merge feeds by session time with an explicit stable tie-break using index feed order and per-feed record ordinal. The reader should expose keyframes only as separately labeled snapshots and must never inject them into an earlier replay position.

### Season acquisition result — 2026-08-18

The raw fixture set now covers every non-practice session in the official 2026 season index: 30 sessions across all 11 race meetings from Australia through Hungary. This includes each Grand Prix qualifying and race plus Sprint Qualifying and Sprint for China, Miami, Canada, and Britain. The two pre-season testing meetings contain only practice sessions and were intentionally skipped. Previously downloaded Grand Prix practice directories were removed at the user's request and were not restored.

The 30 session directories under `companion/raw/` contain 30 session indexes and all 887 unique referenced `StreamPath` files: 917 files and 518,598,988 bytes in total. The files contain 2,721,963 timestamped records, including 367,744 compressed car/position frames. All local stream byte counts and MD5 digests match the official archive's `Content-Length` and S3 `ETag`; no indexed streams are missing and no extra files exist inside the session directories.

Every retained session passed the same structural checks as the initial Hungary race fixture: UTF-8 BOM, CRLF framing, final CRLF, fixed-width session timestamp, nondecreasing per-feed ordering, JSON object payloads, and strict Base64 plus raw-DEFLATE plus JSON decoding for `.z` feeds. The feed inventory evolved during the season: earlier qualifying/race sessions contain 26/32 streams while later sessions contain 27/33, so the reader must use each session's index rather than assume a fixed topic list.

No `KeyFramePath` snapshots were downloaded, and no processor or UI implementation was started. The deterministic raw reader described above remains the next implementation step.
