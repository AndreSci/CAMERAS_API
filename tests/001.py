import datetime
cam_name = "cam1"

date_time = str(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))

print(f"{cam_name}-{date_time}")