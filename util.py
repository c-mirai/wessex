# Wessex - A log-reading bot for mordhau.
# Copyright (C) 2021  Morgan Chesser mfreelancedef@gmail.com

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import datetime


def timestamp_to_datetime(timestamp):
	#[2021.01.09-22.17.01:079]
	#"%Y.%m.%d-%H.%M.%S:%f"
	#dt = datetime.datetime()
	dt = datetime.datetime.strptime(timestamp, "%Y.%m.%d-%H.%M.%S:%f")
	return dt