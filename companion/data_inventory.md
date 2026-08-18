# 2026 Hungarian Grand Prix Raw Data Inventory

Status: Initial availability inventory for planning. This is based on a full scan of the archived qualifying and race streams; it is not yet a normative schema or a complete semantic reference.

## Scope

| Session | Directory | Indexed streams | Timestamped records | Raw bytes including `Index.json` |
| --- | --- | ---: | ---: | ---: |
| Qualifying | `raw/2026-hungary-qualifying/` | 27 | 30,098 | 8,744,703 |
| Race | `raw/2026-hungary-race/` | 33 | 203,569 | 30,611,647 |

The race adds six streams that are absent from qualifying: `ChampionshipPrediction`, `LapCount`, `DriverRaceInfo`, `OvertakeSeries`, `PitStop`, and `PitStopSeries`.

## Format shared by the stream files

- `Index.json` maps each feed name to a `StreamPath` and a `KeyFramePath`. Only the timestamped `StreamPath` files are present locally; the referenced keyframe snapshots were intentionally not downloaded.
- Every downloaded file begins with a UTF-8 BOM. Stream records are CRLF-delimited.
- Each stream record starts with a fixed 12-byte session timestamp such as `00:42:17.123`, immediately followed by one JSON value.
- Stream payloads are sparse incremental updates, not guaranteed full snapshots. Driver numbers, stint numbers, series indexes, and similar identifiers often appear as dynamic object keys. Some feeds use `_deleted` tombstones.
- Many payloads also carry a source `Utc` or `Timestamp`. The line prefix is the archive/replay ordering time; embedded timestamps identify source data time.
- `CarData.z.jsonStream` and `Position.z.jsonStream` have an extra encoding layer: the outer JSON value is a Base64 string whose decoded bytes are raw DEFLATE; inflating it produces the JSON described below.
- Record counts below are physical stream lines. One compressed record can contain multiple telemetry or position samples and multiple cars.
- Field names and value descriptions are the union observed in these two files. Missing, empty, and type-varying values must be expected until a formal schema is defined.

## Session, clock, status, and weather

| File | Q records | Race records | Available contents |
| --- | ---: | ---: | --- |
| `Index.json` | — | — | `Feeds` map with feed names and their `KeyFramePath` and `StreamPath`. It lists 27 qualifying feeds and 33 race feeds. |
| `SessionInfo.jsonStream` | 3 | 3 | Meeting identity and branding; meeting key, name, official name, round number, location, country key/code/name, circuit key/short name; session key, type, name, start/end date, GMT offset, archive path, session status, and archive status. |
| `ArchiveStatus.jsonStream` | 1 | 1 | Archive-generation `Status`. The observed value in both fixtures is `Generating`; this should not be treated as a reliable final-completeness signal by itself. |
| `SessionStatus.jsonStream` | 11 | 5 | Session lifecycle updates in `Status` and `Started`. Observed states include `Inactive`, `Started`, `Finished`, `Finalised`, and `Ends`. Qualifying contains separate transitions for Q1, Q2, and Q3. |
| `SessionData.jsonStream` | 25 | 86 | Timestamped `Series` and `StatusSeries` entries with `Utc`, `SessionStatus`, and `TrackStatus`. Qualifying includes `QualifyingPart` values 0–3; the race includes `Lap` values 1–70. |
| `ExtrapolatedClock.jsonStream` | 9 | 2 | Clock anchor `Utc`, session/segment `Remaining` time, and `Extrapolating`. Qualifying resets the clock for each segment. |
| `Heartbeat.jsonStream` | 386 | 708 | Source heartbeat `Utc` values; useful for liveness and source-time alignment, but it carries no timing/classification state. |
| `TrackStatus.jsonStream` | 11 | 12 | Numeric `Status` plus readable `Message`. Qualifying observes `AllClear` and `Yellow`; the race additionally observes `VSCDeployed` and `VSCEnding`. |
| `LapCount.jsonStream` | — | 70 | Race `CurrentLap` and `TotalLaps` (70 for this event). |
| `WeatherData.jsonStream` | 76 | 157 | Point-in-time weather values: `AirTemp`, `TrackTemp`, `Humidity`, `Pressure`, `Rainfall`, `WindDirection`, and `WindSpeed`. Values are encoded as strings. |
| `WeatherDataSeries.jsonStream` | 76 | 157 | Indexed historical `Series`; each entry has `Timestamp` and a nested `Weather` object containing the same seven weather fields. |

## Drivers, classification, and timing

| File | Q records | Race records | Available contents |
| --- | ---: | ---: | --- |
| `DriverList.jsonStream` | 144 | 211 | Driver-number-keyed identity and team metadata: `RacingNumber`, `Tla`, broadcast/full/first/last names, `Reference`, `TeamName`, `TeamColour`, `HeadshotUrl`, display `Line`, and `PublicIdRight`. Qualifying also contains `_deleted` patches. |
| `TimingData.jsonStream` | 8,634 | 71,303 | Main sparse timing/classification feed. Per-driver data includes line/position, racing number, show-position, retired/stopped/in-pit/pit-out state, lap and pit-stop counts, status flags, last/best lap, three sectors, mini-segment status arrays, speed traps (`I1`, `I2`, `FL`, `ST`), fastest/personal-best flags, and previous values. Race data adds gap to leader and interval/catching. Qualifying adds session part, cutoff/no-entry data, knockout/cutoff state, per-segment best laps, and differences to fastest/ahead. |
| `TimingDataF1.jsonStream` | 8,634 | 40,878 | A second timing stream with the same observed field vocabulary as `TimingData`. In Hungary qualifying the two files are byte-for-byte identical. In the race they are not: `TimingDataF1` has fewer updates and fewer status combinations. Its intended relationship to `TimingData` still needs to be established before choosing a canonical source. |
| `TimingStats.jsonStream` | 560 | 1,297 | Per-driver statistical bests: `PersonalBestLapTime`, three `BestSectors`, speed-trap `BestSpeeds` at `I1`, `I2`, `FL`, and `ST`, position/line/racing number, session type, withholding, and occasional `_deleted` patches. |
| `TopThree.jsonStream` | 152 | 3,390 | Presentation-ready top-three array with position, driver and team identity/colour, lap time/state, gaps to leader/ahead, show-position, and overall/personal-fastest flags. Qualifying also carries `SessionPart`. |
| `DriverTracker.jsonStream` | 674 | 31,761 | Compact whole-field tracker: position, racing number, lap time/state, gaps to leader/ahead, show-position, and overall/personal-fastest flags. It omits the richer driver/team identity carried by `TopThree` and `DriverList`. Qualifying also carries `SessionPart`. |
| `LapSeries.jsonStream` | 300 | 1,429 | Driver-number-keyed `RacingNumber` plus `LapPosition`, an incrementally updated position-by-lap series suitable for classification history and race trace work. |
| `DriverRaceInfo.jsonStream` | — | 30,428 | High-frequency per-driver race summary: `Position`, `Gap`, `Interval`, `Catching`, `OvertakeState`, `PitStops`, and `IsOut`, keyed by racing number. |

### Important timing overlap

`TimingData`, `TimingDataF1`, `TopThree`, `DriverTracker`, and `DriverRaceInfo` overlap heavily but have different density and presentation. They should not all be normalized independently without first comparing event timing and revision behavior. `TimingData` is the richest candidate source; the other feeds may be useful for validation or for source-specific states not reconstructible from it.

## Tyres and pit activity

| File | Q records | Race records | Available contents |
| --- | ---: | ---: | --- |
| `TimingAppData.jsonStream` | 563 | 1,160 | Driver `Lines` containing stint arrays and timing-app state. Observed stint fields include `Compound`, `New`, `TyresNotChanged`, `StartLaps`, `TotalLaps`, `LapNumber`, `LapTime`, and `LapFlags`; race data also includes `GridPos`. |
| `TyreStintSeries.jsonStream` | 326 | 807 | Driver- and stint-keyed tyre history with `Compound`, `New`, `TyresNotChanged`, `StartLaps`, and `TotalLaps`. Compounds observed are soft, medium, hard, and unknown; hard is race-only in these fixtures. |
| `CurrentTyres.jsonStream` | 62 | 44 | Sparse current tyre updates keyed by driver: `Compound` and `New`. This feed uses JSON booleans for `New`, while the stint feeds encode `New` as strings. |
| `PitLaneTimeCollection.jsonStream` | 196 | 90 | Indexed pit-lane visits containing `RacingNumber`, `Duration`, and `Lap`, plus `_deleted` patches. It is present in both qualifying and race and includes long garage/pit-lane durations, not only racing pit stops. |
| `PitStop.jsonStream` | — | 33 | Flat race pit-stop updates with `RacingNumber`, stationary `PitStopTime`, total `PitLaneTime`, and `Lap`. |
| `PitStopSeries.jsonStream` | — | 34 | Driver- and stop-index-keyed race series. Each entry adds a source `Timestamp` and embeds the same `PitStop` fields as the flat feed. |

## Car telemetry and position

| File | Q records | Race records | Available contents |
| --- | ---: | ---: | --- |
| `CarData.z.jsonStream` | 4,580 | 9,342 | Decoded object contains `Entries[]`; each entry has `Utc` and a `Cars` map keyed by racing number, then numeric `Channels`. Both fixtures contain only channel IDs `0`, `2`, `3`, `4`, and `5`, conventionally RPM, speed, gear, throttle, and brake. No DRS channel is present in these Hungary files. |
| `Position.z.jsonStream` | 4,573 | 9,344 | Decoded object contains `Position[]`; each sample has `Timestamp` and an `Entries` map whose values contain `Status`, `X`, `Y`, and `Z`. Race status includes `OnTrack` and `OffTrack`; qualifying only observes `OnTrack`. Initial frames include many zero-valued placeholder entries. |

The raw car channels need defensive validation before use. In these fixtures throttle/brake values reach 104 rather than a clean 0–100 range, and qualifying has an anomalous gear value of 50. Position coordinates likewise begin with zero placeholders and require filtering/map matching before computing lap progress.

## Race control, championship, and overtakes

| File | Q records | Race records | Available contents |
| --- | ---: | ---: | --- |
| `RaceControlMessages.jsonStream` | 42 | 80 | Structured, indexed messages with `Utc`, `Category`, `Message`, and optional `Flag`, `Scope`, `Sector`, `Lap`, `RacingNumber`, `Status`, and `Mode`. Qualifying contains flag/other messages; race adds driver flags and VSC safety-car state. |
| `TlaRcm.jsonStream` | 42 | 80 | A parallel preformatted race-control text feed with `Timestamp` and `Message`. Record counts match `RaceControlMessages` in both sessions, but correspondence and revision behavior still need explicit verification. |
| `ChampionshipPrediction.jsonStream` | — | 104 | Live projected championship tables. `Drivers` entries contain racing number, current/predicted position, and current/predicted points. `Teams` entries contain team name and the same current/predicted position and points fields. |
| `OvertakeSeries.jsonStream` | — | 516 | Nested `Overtakes` series with indexed `Timestamp` and cumulative `count` values. The meaning of both dynamic key levels and how the count maps to individual overtake events still needs confirmation. |

## Media and commentary references

| File | Q records | Race records | Available contents |
| --- | ---: | ---: | --- |
| `ContentStreams.jsonStream` | 2 | 2 | External content metadata: `Type`, `Name`, `Language`, `Uri`, optional `Path`, and `Utc`. The observed entries are English commentary and live audio references; media is not embedded. |
| `AudioStreams.jsonStream` | 1 | 1 | Live coverage audio playlist metadata: name, language, external HLS `Uri`, relative archive `Path`, and `Utc`. No audio bytes are stored locally. |
| `TeamRadio.jsonStream` | 15 | 34 | Indexed capture metadata with `Utc`, `RacingNumber`, and a relative MP3 `Path`. It lists published transmissions but does not contain or locally store the audio. |

## Planning observations

- A first timing-tower reducer can likely center on `TimingData`, joined with `DriverList`, `TimingAppData`/tyre feeds, `TrackStatus`, `SessionStatus`, and race `LapCount`. The alternate presentation feeds should initially be validators rather than separate sources of truth.
- Qualifying attempt reconstruction has the necessary ingredients: session-part transitions, pit state, lap/sector/mini-segment changes, position samples, car channels, and later race-control messages. Intent such as push versus preparation is still inferred rather than transmitted directly.
- Continuous qualifying delta can use `Position.z` as its core sample stream, with `CarData.z` for plausibility checks. Zero placeholders, off-track samples, clock differences, and anomalous channel values must be handled explicitly.
- Tyre, weather, pit, and race-control data each have overlapping point-update and series forms. Before schema v1, compare their revision timing and select one causal source plus one validation source for each domain.
- Keyframes remain outside this inventory. The processor must reconstruct state from timestamped streams or label any future keyframe use as a non-causal snapshot.

