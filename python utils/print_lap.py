import fastf1
import my_f1_utils # cache
import numpy as np

# session = fastf1.get_session(2026, 1, "R")
# session.load()
# laps = session.laps.pick_drivers("HAM")
# lap = laps[laps["LapNumber"] == 1].iloc[0]
# lap = laps[laps["LapNumber"] == 40]

session = fastf1.get_session(2026, 8, "Q")
session.load()
laps = session.laps.split_qualifying_sessions()[2]
laps = laps.pick_drivers("RUS")
# lap = laps.pick_fastest()
# pick lap 16
lap = laps[laps["LapNumber"] == 19].iloc[0]
# for li,lap in laps.iterlaps():
    # print(lap["LapNumber"], lap["Driver"], lap["LapTime"].total_seconds())

# sector_times = [
#     lap["Sector1Time"].total_seconds(),
#     lap["Sector2Time"].total_seconds(),
#     lap["Sector3Time"].total_seconds(),
# ]
# print(f"{'|'.join(map(str, sector_times))}")

car_data = lap.get_car_data(pad=1, pad_side='both')
car_data_Time = car_data["Time"].dt.total_seconds().to_numpy()
car_data_Speed = car_data["Speed"].to_numpy()
for row in car_data.itertuples():
    print(f"{row.Time.total_seconds()}|{row.Speed}|{row.Throttle}|{row.Brake}|{row.nGear}|{row.RPM}")

# pos_data = lap.get_pos_data(pad=1, pad_side='both')
# for row in pos_data.itertuples():
#     # interpolate the car_data speed and time
#     time = row.Time.total_seconds()
#     speed = np.interp(time, car_data_Time, car_data_Speed)
#     print(f"{time}|{row.X/10}|{row.Y/10}|{row.Z/10}|{speed}")