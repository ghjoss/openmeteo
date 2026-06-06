.# globals.py
# ----- raw user‑provided values -----
QUERY_INTERVAL_MINUTES = 15        # user may edit this
TESTING = True                      # user may edit this
# FORECAST_HOURS: Number of hours to show in the forecast view. Must be between 3 and 9.
FORECAST_HOURS = 9                  # user may edit this
# N_DAY_FORECAST: Number of days to show in the N-day forecast view. Must be between 3 and 7.
N_DAY_FORECAST = 5                     # user may edit this
# START_HOUR: Hours from midnight until this time
#               Will display nothing, unless the screen
#               is touched.

START_HOUR = 4                      # user may edit this

# END_HOUR: Hours from START_HOUR to this hour are
#           active hours. During inactive hours, the
#           screen is dimmed and no polling is done

END_HOUR = 22                       # user may edit this      

# ----- validation helpers -----
def _as_int(value, default):
    """Convert numeric value to int, falling back to default."""
    if isinstance(value, (int, float)):
        return int(value)
    return default

def _as_bool(value, default):
    """Convert string value to bool, falling back to default."""
    if isinstance(value, bool):
        return value
    return default

# ----- validated, public constants -----
try:
    QUERY_INTERVAL = _as_int(QUERY_INTERVAL_MINUTES, 15)
except NameError:
    QUERY_INTERVAL = 15

try:
    TESTING = _as_bool(TESTING, False)
except NameError:
    TESTING = False

# Enforce minimum interval unless we are in testing mode.
if not TESTING:
    def print(*args, **kwargs):
        pass

    if QUERY_INTERVAL < 15:
        QUERY_INTERVAL = 15

try:
    FORECAST_HOURS = _as_int(FORECAST_HOURS, 9)
except NameError:
    FORECAST_HOURS = 9

try:
    START_HOUR = _as_int(START_HOUR, 6)
    if START_HOUR < 0 or START_HOUR > 23:
        START_HOUR = 0
except NameError:
    START_HOUR = 6
except ValueError:
    START_HOUR = 0


try:
    END_HOUR = _as_int(END_HOUR, 22)
    if END_HOUR < 0 or END_HOUR > 23:
        END_HOUR = 23
except NameError:
    END_HOUR = 22
except ValueError:
    END_HOUR = 23

try:
    N_DAY_FORECAST = _as_int(N_DAY_FORECAST, 3)
except NameError:
    N_DAY_FORECAST = 3

if N_DAY_FORECAST < 3 or N_DAY_FORECAST > 7:
    N_DAY_FORECAST = 3
