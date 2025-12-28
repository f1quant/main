import fastf1, fastf1.api, pandas as pd, numpy as np
import my_f1_utils  # caching

def load_timing_stream(session, abbrevs):
    _, stream_data = fastf1.api.timing_data(session.api_path)
    df = stream_data[["Time", "Driver", "Position"]].copy()
    df = df.sort_values("Time")
    df = df.rename(columns={"Driver": "DriverNumber"})
    df["Driver"] = df["DriverNumber"].map(abbrevs)  # driver abbrev
    return df

def identify_overtakes(stream_df):
    positions = {}
    prev_order = None
    overtakes = []
    for t, group in stream_df.groupby("Time", sort=True):
        for _, row in group.iterrows():
            drv = row["Driver"]          # abbreviation
            pos = int(row["Position"])
            positions[drv] = pos
        current_order = sorted(positions.keys(), key=lambda d: positions[d])
        if prev_order is not None:
            prev_idx = {d: i for i, d in enumerate(prev_order)}
            for i in range(len(current_order) - 1):
                d1 = current_order[i]      # ahead (potential overtaker)
                d2 = current_order[i + 1]  # behind (potential overtaken)

                if d1 not in prev_idx or d2 not in prev_idx: continue
                if prev_idx[d1] > prev_idx[d2]:
                    overtakes.append((t, d1, d2, positions[d1]))
        prev_order = current_order
    return overtakes

def build_pos_lookup(session):
    raw_pos = fastf1.api.position_data(session.api_path)  # dict keyed by car number
    lookup = {}
    results = session.results
    for _, row in results.iterrows():
        car_num = str(row["DriverNumber"])
        drv_abbr = row["Abbreviation"]
        df = raw_pos[car_num].copy()
        df = df.sort_values("Time")
        df = df[["Time", "X", "Y"]].set_index("Time")
        df = df.astype(float)
        lookup[drv_abbr] = df
    return lookup

def get_xy_at_time(pos_lookup, driver, t_sec):
    df = pos_lookup[driver]
    times = df.index.total_seconds().to_numpy()
    xs = df["X"].to_numpy()
    ys = df["Y"].to_numpy()
    x = float(np.interp(t_sec, times, xs))
    y = float(np.interp(t_sec, times, ys))
    return x, y

def build_corner_array(session):
    ci = session.get_circuit_info()
    corners = ci.corners  # DataFrame-like with X, Y (and usually Number)
    xs = corners["X"].to_numpy(dtype=float)
    ys = corners["Y"].to_numpy(dtype=float)
    labels = corners["Number"].astype(str).to_numpy()
    return xs, ys, labels

def closest_corner(xs_c, ys_c, labels, x, y):
    dx = xs_c - x
    dy = ys_c - y
    dists = np.hypot(dx, dy)
    idx = int(np.argmin(dists))
    return labels[idx], float(dists[idx])

def build_lap_lookup(session):
    laps = session.laps
    lap_lookup = {}
    for drv, grp in laps.groupby("Driver"):  # driver abbreviations
        df = grp[["LapNumber", "LapStartTime"]].copy().sort_values("LapStartTime")
        lap_lookup[drv] = df
    return lap_lookup

def get_lap_at_time(lap_lookup, driver, t_sec):
    df = lap_lookup[driver]
    start_secs = df["LapStartTime"].dt.total_seconds().to_numpy()
    lap_nums = df["LapNumber"].to_numpy()
    idx = np.searchsorted(start_secs, t_sec, side="right") - 1
    if idx < 0: return None
    return int(lap_nums[idx])

def build_pit_intervals(session):
    laps = session.laps

    pit_lookup = {abbr: [] for abbr in session.results["Abbreviation"].tolist()}
    for drv, grp in laps.groupby("Driver"):
        ins = grp["PitInTime"].dropna().sort_values().reset_index(drop=True)
        outs = grp["PitOutTime"].dropna().sort_values().reset_index(drop=True)

        intervals = []
        j = 0  # pointer into outs

        for start_td in ins:
            # Find the first pit-out strictly after this pit-in
            while j < len(outs) and outs.iloc[j] <= start_td:
                j += 1

            if j < len(outs):
                end_td = outs.iloc[j]
                j += 1
            else:
                # If no PitOutTime is available, close at the last known lap time for that driver
                end_td = grp["Time"].dropna().max()
                if pd.isna(end_td):
                    end_td = grp["LapStartTime"].dropna().max()
                if pd.isna(end_td):
                    end_td = start_td  # fallback

            intervals.append((float(start_td.total_seconds()), float(end_td.total_seconds())))

        pit_lookup[drv] = intervals

    return pit_lookup

def is_in_pit(pit_lookup, driver, t_sec, margin=0.0):
    intervals = pit_lookup.get(driver, [])
    for start, end in intervals:
        if start - margin <= t_sec <= end + margin:
            return True
    return False

def last_lap_by_driver(session):
    ans = {}
    for driver, grp in session.laps.groupby("Driver"):
        last_lap = grp.sort_values("LapNumber").iloc[-1]
        ans[driver] = int(last_lap["LapNumber"])
    return ans

def main():
    year, round_no, session_type = 2024, "Canada", "R"
    session = fastf1.get_session(year, round_no, session_type)
    session.load()

    last_laps = last_lap_by_driver(session)

    abbrevs = {}
    for _, row in session.results.iterrows():
        # print(f"{row['DriverNumber']}|{row['Abbreviation']}")
        abbrevs[row["DriverNumber"]] = row["Abbreviation"]

    pos_lookup = build_pos_lookup(session)
    stream_df = load_timing_stream(session, abbrevs)
    overtakes = identify_overtakes(stream_df)

    corner_xs, corner_ys, corner_labels = build_corner_array(session)
    lap_lookup = build_lap_lookup(session)
    pit_lookup = build_pit_intervals(session)

    print("time_s|lap|overtaker|new_pos|x|y|corner|dist|overtaken|x|y|corner|dist|in_pit")

    for t_td, d1, d2, new_pos in overtakes:
        t_sec = t_td.total_seconds()
        x1, y1 = get_xy_at_time(pos_lookup, d1, t_sec)
        x2, y2 = get_xy_at_time(pos_lookup, d2, t_sec)
        c1_label, c1_dist = closest_corner(corner_xs, corner_ys, corner_labels, x1, y1)
        c2_label, c2_dist = closest_corner(corner_xs, corner_ys, corner_labels, x2, y2)
        lap = get_lap_at_time(lap_lookup, d1, t_sec)
        overtaken_in_pit = is_in_pit(pit_lookup, d2, t_sec, margin=0.5)
        if overtaken_in_pit: continue
        if lap == 1: continue  # ignore first lap overtakes
        lap2 = get_lap_at_time(lap_lookup, d2, t_sec)
        if last_laps[d2] - lap2 in [0,1]: continue

        print(
            f"{t_sec}|{lap}|"
            f"{d1}|{new_pos}|{x1}|{y1}|{c1_label}|{c1_dist}|"
            f"{d2}|{x2}|{y2}|{c2_label}|{c2_dist}|{overtaken_in_pit}"
        )

my_f1_utils.setup_cache(offline=False)
main()