import json
import os
import machine

# Shared global dictionary for runtime configurations
settings = {}

CONFIG_FILE = "config.json"

DEFAULTS = {
    "QUERY_INTERVAL_MINUTES": 15,
    "DEBUG": False,
    "N_DAY_FORECAST": 5,
    "START_HOUR": 4,
    "END_HOUR": 22,
    "LATITUDE": 51,
    "LONGITUDE": 0,
    "LOCAL_LATITUDE": 51,
    "LOCAL_LONGITUDE": 0,
    "TIMEZONE": "auto",
    "UNITS": "imperial",  # imperial / metric
    "OPEN_STREETMAP_AGENT": "MeteoWeather/V1 (me@domain.com)",
    "TITLE_COLOR": "_RoyalBlue",
    "CHART_DATA_COLOR_TEMP": "_Red",
    "CHART_DATA_COLOR_PRECIP": "_Green",
    "CHART_GRID_COLOR": "_LightGray",
    "CHART_BACKGROUND_COLOR": "_White",
    "TABLE_HEADER_COLOR": "_SlateBlue",
    "TABLE_NORMAL_TEXT_COLOR": "_PaleTurquoise",
    "TABLE_ALERT_TEXT_COLOR": "_Coral",
    "TABLE_BACKGROUND_COLOR":"_Black",
}

# ----- validation helpers -----
def _as_int(value, default):
    """Convert numeric value to int, falling back to default."""
    #log_debug("[control] _as_int()")
    if isinstance(value, (int, float)):
        return int(value)
    return default

def _as_bool(value, default):
    """Convert value to bool, falling back to default."""
    #log_debug("[control] _as_bool()")
    if isinstance(value, bool):
        return value
    return default

def _as_float(value, default):
    """Convert value to float, falling back to default."""
    #log_debug("[control] _as_float()")
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
def _as_str(value,default):
    #log_debug("[control] _as_str()")
    try:
        if value:
            return value
    except (NameError):
        return default

# RP2040 and RP2350 USB Controller base address + SIE_STATUS offset
SIE_STATUS_REG = 0x50110000 + 0x50

# Bit definitions for the SIE status
# Bit 16 (0x10000): Device is connected to a host (handshake completed)
# Bit 4  (0x10): Device is suspended by the host (PC went to sleep or dropped terminal)
SIE_CONNECTED = 1 << 16
SIE_SUSPENDED = 1 << 4

def is_usb_connected():
    """Reads the hardware register to check if an active USB host is connected."""
    try: 
        status = machine.mem32[SIE_STATUS_REG]
    # It must be connected, and NOT suspended by the OS host
        return (status & (SIE_CONNECTED | SIE_SUSPENDED)) == SIE_CONNECTED
    except:
        # Absolute fallback to ensure the app never crashes under power anomalies
        return False

def log_debug(msg):
    
    DEBUG = settings.get("DEBUG", False)
    
    if not DEBUG:
        return
    
    # Check the physical hardware before pushing to the serial buffer
    if is_usb_connected():
        print(f"DEBUG: {msg}")

async def load_settings_async():
    """
    Asynchronously loads the config file and returns validated constants.
    """
    global settings

    log_debug("[control] load_settings_async()")

    try:
        os.stat(CONFIG_FILE)
        file_exists = True
    except OSError:
        file_exists = False

    if file_exists:
        try:
            with open(CONFIG_FILE, "r") as f:
                raw = json.load(f)
        except Exception:
            log_debug("WARNING: config.json corrupt or unreadable. Using defaults.")
            raw = {}
    else:
        raw = {}
    
    # validatation logic

    settings.clear()
    
    # 1. Validate Debug Mode
    settings["DEBUG"] = _as_bool(raw.get("DEBUG"), DEFAULTS["DEBUG"])
    
    # 2. Query Interval (Enforce minimum of 15 minutes, unless in debug mode)
    query_int = _as_int(raw.get("QUERY_INTERVAL_MINUTES"), DEFAULTS["QUERY_INTERVAL_MINUTES"])
    if not settings["DEBUG"] and query_int < 15:
        query_int = 15
    settings["QUERY_INTERVAL_MINUTES"] = query_int

    # 3. number of days of forecast
    n_day = _as_int(raw.get("N_DAY_FORECAST"), DEFAULTS["N_DAY_FORECAST"])
    settings["N_DAY_FORECAST"] = n_day if 3 <= n_day <= 7 else DEFAULTS["N_DAY_FORECAST"]

    # 4. Operating Hours Bounds
    start = _as_int(raw.get("START_HOUR"), DEFAULTS["START_HOUR"])
    settings["START_HOUR"] = start if 0 <= start <= 23 else DEFAULTS["START_HOUR"]

    end = _as_int(raw.get("END_HOUR"), DEFAULTS["END_HOUR"])
    settings["END_HOUR"] = end if 0 <= end <= 23 else DEFAULTS["END_HOUR"]

    # 5. Coordinates
    settings["LATITUDE"] = _as_float(raw.get("LATITUDE"), DEFAULTS["LATITUDE"])
    settings["LONGITUDE"] = _as_float(raw.get("LONGITUDE"), DEFAULTS["LONGITUDE"])

    # 6. Timezone
    tz = raw.get("TIMEZONE") # no validation of timezone as it can have many value
    
    # 7. Units
    units = raw.get("UNITS")
    settings["UNITS"] = units if units in ["imperial", "metric"] else DEFAULTS["UNITS"]
    log_debug("[load_settings_async] settings: {settings}")

    # 8. Clock settings, set LONGITUDE and LATITUDE for clock. THis is separate from the
    #    weather longitude and latitude and is used to manage START_HOUR and END_HOUR
    #    processing.
    settings["LOCAL_LONGITUDE"] = _as_float(raw.get("LOCAL_LONGITUDE"), DEFAULTS["LOCAL_LONGITUDE"])
    settings["LOCAL_LATITUDE"] = _as_float(raw.get("LOCAL_LATITUDE"), DEFAULTS["LOCAL_LATITUDE"])
    # 9. Color settings
    settings["TITLE_COLOR"] = _as_str(raw.get("TITLE_COLOR"), DEFAULTS["TITLE_COLOR"])
    settings["CHART_DATA_COLOR_TEMP"] = _as_str(raw.get("CHART_DATA_COLOR_TEMP"), DEFAULTS["CHART_DATA_COLOR_TEMP"])   
    settings["CHART_DATA_COLOR_PRECIP"] = _as_str(raw.get("CHART_DATA_COLOR_PRECIP"), DEFAULTS["CHART_DATA_COLOR_PRECIP"])
    settings["CHART_GRID_COLOR"] = _as_str(raw.get("CHART_GRID_COLOR"), DEFAULTS["CHART_GRID_COLOR"])
    settings["CHART_BACKGROUND_COLOR"] = _as_str(raw.get("CHART_BACKGROUND_COLOR"), DEFAULTS["CHART_BACKGROUND_COLOR"])
    settings["TABLE_HEADER_COLOR"] = _as_str(raw.get("TABLE_HEADER_COLOR"), DEFAULTS["TABLE_HEADER_COLOR"])
    settings["TABLE_NORMAL_TEXT_COLOR"] = _as_str(raw.get("TABLE_NORMAL_TEXT_COLOR"), DEFAULTS["TABLE_NORMAL_TEXT_COLOR"])
    settings["TABLE_ALERT_TEXT_COLOR"] = _as_str(raw.get("TABLE_ALERT_TEXT_COLOR"), DEFAULTS["TABLE_ALERT_TEXT_COLOR"])
    settings["TABLE_BACKGROUND_COLOR"] = _as_str(raw.get("TABLE_BACKGROUND_COLOR"), DEFAULTS["TABLE_BACKGROUND_COLOR"])

    # 10. WiFi Settings
    settings["WIFI_SSID"] = _as_str(raw.get("WIFI_SSID"), None)
    settings["WIFI_PASSWORD"] = _as_str(raw.get("WIFI_PASSWORD"), None)

    # 11. OpenStreetMap Agent
    settings["OPEN_STREETMAP_AGENT"] = _as_str(raw.get("OPEN_STREETMAP_AGENT"), DEFAULTS["OPEN_STREETMAP_AGENT"])
    return settings

async def save_settings_async(new_data):
    """
    saves data back to config.json
    """
    log_debug("[control] save_settings_async()")
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(new_data, f)
        return True
    except OSError as e:
        log_debug("ERROR: could not save configuration")
    except Exception as e:
        log_debug(f"ERROR: {e}")
    return False
