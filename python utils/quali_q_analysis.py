import pandas as pd
all_df_q = pd.read_csv('github/all_df_q.csv', low_memory=False)
all_df_q = all_df_q[all_df_q["session_type"] == "Q"]
all_df_q = all_df_q[all_df_q["lap_Deleted"] == False]
all_df_q = all_df_q[all_df_q["lap_LapTime"].notna()]

for (year,round_no), quali_laps in all_df_q.groupby(["year", "round_no"]):
    # calculate each drivers best lap time by session and position by session
    best_by_session = {}
    position_by_session = {}
    for session in [1,2,3]:
        best_by_session[session] = {}
        q_laps = quali_laps[quali_laps["quali_session"] == session]
        for driver, driver_q_laps in q_laps.groupby("lap_Driver"):
            best_by_session[session][driver] = driver_q_laps["lap_LapTime"].min()

        position_by_session[session] = {}
        sorted_drivers = sorted(best_by_session[session].items(), key=lambda x: x[1])
        for pos, (driver, time) in enumerate(sorted_drivers, start=1):
            position_by_session[session][driver] = pos
    
    q3_drivers = sorted(list(best_by_session[3].keys()), key=lambda d: position_by_session[3][d])
    for d1 in range(len(q3_drivers)):
        for d2 in range(d1+1, len(q3_drivers)):
            driver1, driver2 = q3_drivers[d1], q3_drivers[d2]
            diff_by_session = [best_by_session[x].get(driver1) - best_by_session[x].get(driver2) for x in [1,2,3]]
            if abs(diff_by_session[2]) > 5: continue
            # print(f"{year}|{round_no}|{driver1}|{position_by_session[3][driver1]}|{driver2}|{position_by_session[3][driver2]}|{diff_by_session[0]}|{diff_by_session[1]}|{diff_by_session[2]}")
    
    for driver in q3_drivers:
        if best_by_session[1][driver] - best_by_session[3][driver] < -5: continue
        print(f"{year}|{round_no}|{driver}|{position_by_session[1][driver]}|{position_by_session[2][driver]}|{position_by_session[3][driver]}|{best_by_session[1][driver]}|{best_by_session[2][driver]}|{best_by_session[3][driver]}")
        