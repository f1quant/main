import fastf1
import my_f1_utils # cache
import numpy as np

session = fastf1.get_session(2026, 2, "SQ")
session.load()
laps = session.laps.split_qualifying_sessions()[2]
nor_laps = laps.pick_drivers("NOR")
nor_lap = nor_laps.pick_fastest()

rus_laps = laps.pick_drivers("RUS")
rus_lap = rus_laps.pick_fastest()


speed_tables = {}
for lap in [nor_lap, rus_lap]:
    # build a table of x|y|z|speed
    car_data = lap.get_car_data(pad=1, pad_side='both')
    car_data_Time = car_data["Time"].dt.total_seconds().to_numpy()
    car_data_Speed = car_data["Speed"].to_numpy()
    
    pos_data = lap.get_pos_data(pad=1, pad_side='both')
    pos_data_Time = pos_data["Time"].dt.total_seconds().to_numpy()
    pos_data_X = pos_data["X"].to_numpy()/10
    pos_data_Y = pos_data["Y"].to_numpy()/10
    pos_data_Z = pos_data["Z"].to_numpy()/10
    pos_data_Speed = np.interp(pos_data_Time, car_data_Time, car_data_Speed)
    
    speed_tables[lap["Driver"]] = (pos_data_Time, pos_data_X, pos_data_Y, pos_data_Z, pos_data_Speed)
    # for i in range(len(pos_data_Time)):
    #     print(f"{pos_data_Time[i]}|{pos_data_X[i]}|{pos_data_Y[i]}|{pos_data_Z[i]}|{pos_data_Speed[i]}")

for i in range(len(speed_tables["NOR"][0])):
    # find the closest (x,y,z) in the RUS table
    dists = np.sqrt((speed_tables["RUS"][1] - speed_tables["NOR"][1][i])**2 + (speed_tables["RUS"][2] - speed_tables["NOR"][2][i])**2 + (speed_tables["RUS"][3] - speed_tables["NOR"][3][i])**2)
    closest_index = np.argmin(dists)
    print(f"{speed_tables['NOR'][0][i]}|{speed_tables['NOR'][1][i]}|{speed_tables['NOR'][2][i]}|{speed_tables['NOR'][3][i]}|{speed_tables['NOR'][4][i]}|{speed_tables['RUS'][0][closest_index]}|{speed_tables['RUS'][1][closest_index]}|{speed_tables['RUS'][2][closest_index]}|{speed_tables['RUS'][3][closest_index]}|{speed_tables['RUS'][4][closest_index]}")