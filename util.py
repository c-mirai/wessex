import datetime


def timestamp_to_datetime(timestamp):
	#[2021.01.09-22.17.01:079]
	#"%Y.%m.%d-%H.%M.%S:%f"
	#dt = datetime.datetime()
	dt = datetime.datetime.strptime(timestamp, "%Y.%m.%d-%H.%M.%S:%f")
	return dt