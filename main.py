import time
import asyncio
import gc
from control import settings, log_debug, load_settings_async, save_settings_async, DEFAULTS
import display_functions as df
from presto import Presto
import picovector
import openmeteo
import ntptime
import urequests as requests
#---------------------
# wifi requirements
import network
import ubinascii
#---------------------

def wifi_connect(settings):
    """
    Connect to the wifi network using the SSID and PASSWORD

    Args:
        none

    Returns:
        The network.WLAN object instantiated
    """
    try:
        DEBUG = settings.get("DEBUG", False)
    except:
        DEBUG = True

    log_debug("[network_access] wifi_connect()")
    WIFI_SSID = settings.get("WIFI_SSID")
    WIFI_PASSWORD = settings.get("WIFI_PASSWORD")
    wlan = network.WLAN(network.WLAN.IF_STA)
    
    # ensure that the network does not have a currently active connection
    wlan.active(False)
    time.sleep(1.0)
    
    # reinitialize
    wlan.active(True)

    # CRITICAL: Disable wireless power management to stop the RM2 chip 
    # from dropping into low-power sags on standalone power.
    # Passing -1592655711 is the exact signed 32-bit equivalent of 0xA11140A1
    try:
        wlan.config(pm=0xA11140A1 & 0xFFFFFFFF) # Mask explicitly to unsigned word
    except OverflowError:
        try:
            # Fallback for standard 32-bit signed long conversion edge cases
            wlan.config(pm=-1592655711) 
        except Exception as e:
            log_debug(f"[Power Config Error] Signed/Unsigned fallback failed: {e}")                 
    #clear any left-overs
    wlan.disconnect()
    time.sleep(1.0)

    if DEBUG:
        try:
            rawMac = wlan.config('mac')
            hexMac = ubinascii.hexlify(rawMac).decode('utf-8')
            standardMac = ":".join(["{:02X}".format(b) for b in rawMac])
            log_debug("="*40)
            log_debug(f"RP2350 Raw Bytes: {rawMac}")
            log_debug(f"Hex String:       {hexMac}")
            log_debug(f"Standard MAC:     {standardMac}")
            log_debug("="*40)    
        except Exception as e:
            log_debug(f"[MAC read error]   Failed to poll hardware MAC {e}")
        try:
            # Pull module/driver configuration strings if available
            log_debug(f"[Tx Power Rating]  {wlan.config('txpower')} dBm")
        except Exception:
            pass

        # 2. THE AIRWAVE ENVIROMENT (SCAN DETAILED RESULTS)
        log_debug("[RF Environment Scan] Searching for networks...")
        try:
            scan_results = wlan.scan()
            log_debug(f" -> Found {len(scan_results)} visible wireless nodes.")
            
            target_found = False
            for net in scan_results:
                ssid = net[0].decode('utf-8')
                bssid = ubinascii.hexlify(net[1], ':').decode().upper()
                channel = net[2]
                rssi = net[3]
                security = net[4]
                
                # Print a concise list of matching or nearby networks
                if ssid == WIFI_SSID or rssi > -60:
                    log_debug(f"    * SSID: {ssid:<15} | BSSID: {bssid} | Chan: {channel:<2} | RSSI: {rssi}dBm")
                    if ssid == WIFI_SSID:
                        target_found = True
                        log_debug(f"{ssid} router SSID matched")
            if not target_found:
                log_debug(f" [!] CRITICAL WARNING: Target SSID '{WIFI_SSID}' was NOT detected in the airwave scan!")
        except Exception as e:
            log_debug(f" [!] SCAN CRASHED: SPI Bus lockup or hardware unresponsive: {e}")
    # Standalone Network Connection Loop
    attempts = 2
    while attempts > 0:

        log_debug(f"Initiating connection handshake to: {WIFI_SSID}")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        # Wait for the connection to actually establish (Up to 15 seconds)
        max_wait = 15
        while max_wait > 0:
            status = wlan.status()
            # Check for a terminal connection state (STAT_GOT_IP is typically 3)
            if status == 3 or status == network.STAT_GOT_IP: 
                break
            if status < 0: # Connection failed explicitly or dropped out
                break
            max_wait -= 1
            time.sleep(1)

        if wlan.status() == network.STAT_GOT_IP:
            log_debug(f"Successfully linked! IP Address: {wlan.ifconfig()[0]}")
            return wlan
            
        attempts -= 1
        log_debug(f"Connection attempt timed out. Status code: {wlan.status()}")
        if attempts > 0:
            log_debug("Recycling wireless interface for retry...")
            wlan.active(False)
            time.sleep(1.5)
            wlan.active(True)
            try:
                wlan.config(pm=0xA11140A1)
            except Exception:
                pass
            wlan.disconnect()
            time.sleep(1.0)
            
    log_debug("CRITICAL: FAILED to acquire an active IP configuration.")
    return None

def get_city(lcl_settings):
    """
    using the passed settings, extract longitude and latitude, query openstreetmap for the
    city name.

    This routine is called during app initialization and again whenever the
    web page updates parameters, in case longitude or latitude changed.
    """
    log_debug("[main] get_city()")
    # use longitude and latitude to get the city name
    log_debug("openstreetmap city name request (one-time call)...")
    
    latitude = lcl_settings.get("LATITUDE", 0.0)
    longitude = lcl_settings.get("LONGITUDE", 0.0)
    agent = lcl_settings.get("OPEN_STREETMAP_AGENT")
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}"
    headers = {"User-Agent": f"{agent}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            address = data.get("address", {})
            city = address.get("city") or address.get("town") or address.get("village")
            log_debug(f"City: {city}")
        else:
            log_debug(f"Error: {response.status_code}")
            city = "Forecast"
        response.close()
    except Exception as e:
        city = "Forecast"
        log_debug(f"openstreet map city lookup failed.")
    return city

async def get_local_hhmm(utc_offset_seconds=0):
    """
    Determine the local current time. Assumes the time.io LOCAL_UTC_OFFSET_SECONDS
    was correct, otherwise returns time of day at the prime meridian.

    Args: None
    Returns:
        list: A list containing the current hour and minute [hour, minute].
    """
    log_debug("[main] get_local_hhmm()")

    now = time.gmtime(time.time() + utc_offset_seconds)

    log_debug(f"It is now {now[3]}:{now[4]} on {now[0]}/{now[1]}/{now[2]}")
    return [now[3],now[4]]
 
def initialize():
    """
    Initialize the weather provider. 
    This function sets up the necessary hardware and software components, including connecting to WiFi, initializing the Presto display, 
    and setting up the weather API provider.

    Returns:
        None
    """
    log_debug("[main] initialize()")
    # hardware globals
    global presto, display, vector, brightness


    # software globals
    global connected, query_interval, now, city, local_city, settings_values_changed,brightness

    global current_view_state, FORECAST_VIEW, CURRENT_WEATHER_VIEW, PRECIPITATION_VIEW, N_DAYS_FORECAST_VIEW
    global FORECAST_CHART_VIEW, PRECIPITATION_CHART_VIEW,VIEW_STATES,PARAMETERS
    
    global settings, DEFAULTS
    global termination_flag

    termination_flag = False # set to True on 'Stop' in an IDE's interactive debug mode
    query_interval = settings.get("QUERY_INTERVAL_MINUTES",DEFAULTS["QUERY_INTERVAL_MINUTES"])

    settings_values_changed = False
    # LONGITUDE and LATITUDE are used to query openmeteo for the weather conditions
    LONGITUDE = settings.get("LONGITUDE",DEFAULTS["LONGITUDE"])
    LATITUDE = settings.get("LATITUDE",DEFAULTS["LATITUDE"])

    # LOCAL_LONGITUDE and LOCAL_LATITUDE are used to determine the local time. This is the
    # time used to determine if the app is within the START_HOUR/END_HOUR range.
    LOCAL_LONGITUDE = settings.get("LOCAL_LONGITUDE",DEFAULTS["LOCAL_LONGITUDE"])
    LOCAL_LATITUDE = settings.get("LOCAL_LATITUDE",DEFAULTS["LOCAL_LATITUDE"])

    global START_HOUR, END_HOUR, N_DAY_FORECAST

    START_HOUR = settings.get("START_HOUR", DEFAULTS["START_HOUR"])
    END_HOUR = settings.get("END_HOUR", DEFAULTS["END_HOUR"])
    N_DAY_FORECAST = settings.get("N_DAY_FORECAST", DEFAULTS["N_DAY_FORECAST"]) 

    CURRENT_WEATHER_VIEW = 3
    PRECIPITATION_VIEW = 2
    N_DAYS_FORECAST_VIEW = 0
    FORECAST_VIEW = 4
    FORECAST_CHART_VIEW = 5
    PRECIPITATION_CHART_VIEW = 1
    PARAMETERS = 6
    VIEW_STATES = 7

    log_debug("Starting...")

    # connect to WiFi
    log_debug("Connecting to WiFi...")
    connected = False
    netLan = wifi_connect(settings)

    if netLan is None:
        msg = "Unable to connect to WiFi network. Program terminating."
        log_debug(msg)
        raise RuntimeError(msg)

    global IP_ADDRESS
    IP_ADDRESS = netLan.ifconfig()[0]
    log_debug(f"...connected! IP: {IP_ADDRESS}")

    connected = True
    
    city = get_city(settings)

    # get UTC offset seconds for the local LONGITUDE and LATITUDE, which will be used to determine when to sleep the display
    log_debug("timeapi.io UTC_OFFSET_SECONDS determination (one time call)...")
    global UTC_OFFSET_SECONDS, LOCAL_UTC_OFFSET_SECONDS
    try:
        url = f"https://timeapi.io/api/timezone/coordinate?latitude={LOCAL_LATITUDE}&longitude={LOCAL_LONGITUDE}"
        res = requests.get(url,timeout=5)
        data = res.json()
        LOCAL_UTC_OFFSET_SECONDS = data["currentUtcOffset"]["seconds"]
    except Exception as e:
        log_debug(f"Unable to get UTC offset seconds for the location, defaulting to 0. Error: {e}")
        LOCAL_UTC_OFFSET_SECONDS = 0

    ntptime.settime()
    local_hhmm = get_local_hhmm(LOCAL_UTC_OFFSET_SECONDS)

    log_debug("...UTC_OFFSET complete. Next: Presto initialization...")
    presto = Presto()
    display = presto.display

    display.set_pen(display.create_pen(0,0,0))
    display.clear()

    vector = picovector.PicoVector(display)
    vector.set_antialiasing(picovector.ANTIALIAS_BEST)
    log_debug("...Presto initialized, call display_functions.init_provider...)")
    
    df.init_provider(presto, rotational_shift=-15)

    log_debug("...display provider initialized. Next: call weatherapi.init_provider...)")

    openmeteo.init_provider(presto, settings)
    log_debug("...weather provider initialized")
    brightness = 0.3 # start out at ~1/3
    presto.set_backlight(brightness)
    presto.update()

    return local_hhmm

async def responsive_wait(minutes, data, sleeping, local_hhmm=[0,0], utc_offset_seconds=0):
    """
    Wait for a specified number of minutes while remaining responsive to touch events.
    
    Args:
        minutes (int): The number of minutes to wait.
        data: The weather data.
        sleeping (bool): Whether the display is sleeping.

    Returns:
        None
    """

    log_debug("[main] responsive_wait()")
    global presto, current_view_state, city, settings_values_changed, brightness
    global N_DAY_FORECAST, DEFAULTS, VIEW_STATES
    lcl_data = data
    MIN_SWIPE_DISTANCE = 40
    SWIPE_THRESHOLD = .4
    touch_started = False
    start_time = 0

    start_tick = time.ticks_ms()
    max_ticks = minutes * 60 * 1000

    viewStateChanged = True
    lcl_sleeping = sleeping
    get_weather_once = True
    log_debug(f"Waiting {minutes} min...")
    
    while time.ticks_diff(time.ticks_ms(), start_tick) < max_ticks:
        if not lcl_sleeping:
            # 1. FIX: Added 'await' so the network call actually executes
            if sleeping and get_weather_once: 
                get_weather_once = False
                log_debug("Screen touched outside active hours. Refreshing weather...")
                lcl_data = await get_forecast_with_retries() # Assumed matching signature from main loop
                df.set_backlight(brightness) 

            if viewStateChanged:
                df.cls()
                if current_view_state == FORECAST_VIEW:
                    openmeteo.format_forecast_data(lcl_data, settings)
                elif current_view_state == CURRENT_WEATHER_VIEW:
                    openmeteo.format_current_weather_data(lcl_data, city)
                elif current_view_state == PRECIPITATION_VIEW:
                    openmeteo.format_precipitation_data(lcl_data,settings)
                elif current_view_state == N_DAYS_FORECAST_VIEW:
                    openmeteo.format_N_day_forecast_data(lcl_data, settings)
                elif current_view_state == FORECAST_CHART_VIEW:
                    openmeteo.temp_wind_uv_charts(lcl_data)
                elif current_view_state == PRECIPITATION_CHART_VIEW:
                    openmeteo.precipitation_charts(lcl_data)
                elif current_view_state == PARAMETERS:
                    openmeteo.format_current_parameters(settings, DEFAULTS, city, IP_ADDRESS, utc_offset_seconds)
                viewStateChanged = False

        if settings_values_changed:
            sleeping = False
            break

        presto.touch_poll()
        x, y, touched = presto.touch_a

        if touched:
            if not touch_started:
                touch_started = True
                start_x = x
                start_y = y
                start_time = time.ticks_ms()
        else:
            if touch_started:
                end_x = x
                end_y = y
                dx = end_x - start_x
                adx = abs(dx)
                dy = end_y - start_y
                ady = abs(dy)
                elapsed = time.ticks_diff(time.ticks_ms(), start_time) / 1000
                
                # Wake up local rendering state on any touch interaction
                lcl_sleeping = False 

                if adx < MIN_SWIPE_DISTANCE and ady < MIN_SWIPE_DISTANCE and elapsed < SWIPE_THRESHOLD:
                    log_debug("Tap detected")
                    if current_view_state == PARAMETERS:
                        log_debug("Tap on PARAMETERS view, refreshing screen...")
                        viewStateChanged = True # Force a redraw on tap
                
                elif adx >= ady: # Horizontal Swipes
                    # 3. FIX: Adjusted step direction to match your explicit goal: 
                    # Left swipe adds 1, Right swipe subtracts 1
                    if dx < 0: # Swiped Left (finger moved left)
                        current_view_state = (current_view_state + 1) % VIEW_STATES
                        viewStateChanged = True
                        log_debug("Swiped left, switching view forward.")
                    else: # Swiped Right (finger moved right)
                        current_view_state = (current_view_state - 1) % VIEW_STATES
                        viewStateChanged = True
                        log_debug("Swiped right, switching view backward.")
                else: # Vertical Swipes (Brightness)
                    if dy > 0: 
                        log_debug("swiped down, brightness down...")
                        level_change = -0.05
                    else: 
                        log_debug("swiped up, brightness up...")
                        level_change = 0.05
                    brightness = df.set_backlight(brightness, level_change)
                    log_debug(f"brightness {brightness}")
            
            touch_started = False    

        await asyncio.sleep_ms(20)
        
    # Return the updated data back to weather_loop_task
    return lcl_data


async def in_range(cur_h: int, start_h: int, end_h: int) -> bool:
    """
    Returns True if cur_h (0‑23) lies inside the interval
    [start_h, end_h) on a 24‑hour clock.

    Rules applied:
    • start_h and end_h must be in 0‑23.
    • start_h == end_h → treated as “empty interval” (returns False).
      Change the `if start_h == end_h:` block if you want it to mean
      “always true” (full‑day coverage).
    • If end_h < start_h the interval wraps past midnight (e.g. 23 → 4).
    """
    log_debug("[main] in_range()")
    if start_h == end_h:
        # Empty interval – nothing is inside it.
        # (If you prefer a full‑day interval, simply `return True` here.)
        return False
    # ---- interval check ---------------------------------------
    if start_h < end_h:                       # normal (no wrap‑around)
        active = True if start_h <= cur_h < end_h else False 
    else:                                     # wraps past midnight
        active = True if cur_h >= start_h or cur_h < end_h else False
    log_debug(f"Current Hour: {cur_h}  Starting Hour: {start_h}  Ending Hour: {end_h}  In range: {str(active)}")
    return active

async def get_forecast_with_retries(max_retries=6, initial_interval=400):
    """
    Attempt to retrieve forecast data with retries and exponential backoff.
    If retrieval fails after the specified number of retries, raises a RuntimeError.

    Args:
        max_retries (int): Maximum number of retry attempts.
        initial_interval (int): Initial wait time in milliseconds before the first retry.

    Returns:
        dict: Forecast data if retrieval is successful.

    Raises:
        RuntimeError: If unable to retrieve forecast data after maximum retries.
    """
    log_debug("[main] get_forecast_with_retries()")

    interval = initial_interval
    for attempt in range(max_retries):
        data = await openmeteo.get_forecast_data(settings)
        if data is not None:
            return data
        else:
            log_debug(f"Attempt {attempt + 1} failed. Retrying in {interval} ms...")
            await asyncio.sleep_ms(interval)
            interval *= 2  # Exponential backoff

    raise RuntimeError("Unable to retrieve forecast data after multiple attempts.")

async def weather_loop_task():
    """
    Main weather loop task that continuously fetches and updates weather data.
    This function runs in an infinite loop until the termination_flag is set to True.
    
    Args: None
    Returns: Nothing
    """
    log_debug("[main] weather_loop_task()")

    global settings_values_changed, termination_flag
    global LONGITUDE, LATITUDE, START_HOUR, END_HOUR, N_DAY_FORECAST, LOCAL_UTC_OFFSET_SECONDS
    global query_interval, current_view_state, city, CURRENT_WEATHER_VIEW, brightness
    
    # 1. Setup phase (Runs exactly once)
    is_cold_boot = True
    sleeping = False
    data = None
    current_view_state = CURRENT_WEATHER_VIEW

    # 2. A single, clean loop
    while not termination_flag:
        try:
            # Only read from disk on startup
            if is_cold_boot:
                settings = await load_settings_async()
                is_cold_boot = False

            # Refresh settings from memory
            START_HOUR = settings.get("START_HOUR", 4)
            END_HOUR = settings.get("END_HOUR", 21)
            query_interval = settings.get("QUERY_INTERVAL_MINUTES", 15)
            LONGITUDE = settings.get("LONGITUDE", 0.0)
            LATITUDE = settings.get("LATITUDE", 0.0)
            N_DAY_FORECAST = settings.get("N_DAY_FORECAST", 5)
            
            log_debug("[weather_loop_task] Settings refreshed successfully.")

            if settings_values_changed:
                settings_values_changed = False
                try:
                    city = get_city(settings)
                except Exception:
                    pass

            if not sleeping:
                data = await get_forecast_with_retries()

            local_hhmm = await get_local_hhmm(LOCAL_UTC_OFFSET_SECONDS)
            sleeping = not await in_range(local_hhmm[0], START_HOUR, END_HOUR)

            if sleeping:
                df.cls()
                df.set_backlight(0.0)
            
            # This is where the loop pauses before repeating
            data = await responsive_wait(query_interval, data, sleeping, local_hhmm, utc_offset_seconds=LOCAL_UTC_OFFSET_SECONDS)

        except KeyboardInterrupt:
            log_debug("[weather_loop_task] Program stopped by user. Exiting gracefully.")
            termination_flag = True
            break

        except Exception as e:
            # If any statement above fails, we log it, wait 30s, 
            # and the 'while' loop safely continues to the next iteration
            log_debug(f"[weather_loop_task] Loop stumbled: {e}. Recovering in 30s...")
            try:
                df.presto_errors(f"[weather_loop_task] {e}")
            except Exception:
                pass
            await asyncio.sleep(30)

def render_html(settings):
  """
  Render the HTML page for the configuration interface.
  
  Args:
      settings (dict): A dictionary containing the configuration settings.
  
  Returns:
      str: The rendered HTML string.
  """
  LATITUDE = settings.get("LATITUDE", 0.0)
  LONGITUDE = settings.get("LONGITUDE", 0.0)
  UNITS = settings.get("UNITS", "metric")
  QUERY_INTERVAL_MINUTES = settings.get("QUERY_INTERVAL_MINUTES", 15)
  START_HOUR = settings.get("START_HOUR", 4)
  END_HOUR = settings.get("END_HOUR", 22)
  N_DAY_FORECAST = settings.get("N_DAY_FORECAST", 5)

  return f"""<!DOCTYPE html>
  <html>
  <head>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <title>Presto open-meteo API parameters</title>
    <style>
      body {{ font-family: sans-serif; margin: 20px; background: #f4f4f9; }}
      .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); max-width: 450px; }}
      input, select {{ width: 100%; padding: 8px; margin: 6px 0 12px 0; box-sizing: border-box; }}
      input[type=submit] {{ background: #0078d4; color: white; border: none; cursor: pointer; font-weight: bold; }}
      
      /* Fixed CSS escaping for the f-string */
      .tiny-table {{ 
        width: 100%; 
        font-size: 0.65rem; 
        line-height: 1.2; 
        margin-bottom: 12px; 
        border-collapse: collapse; 
        white-space: nowrap; 
      }}
      .tiny-table td {{ 
        padding: 2px 2px; 
        vertical-align: top; 
      }}
      .tiny-table td.num {{ 
        text-align: right; 
        color: #555; 
      }}
      .tiny {{ font-size: 0.5rem; line-height: 1.2; }}
    </style>
  </head>
  <body>
    <div class="card">
      <h3>Presto Open-Meteo API Parameters</h3>
      <form action="/config" method="get">
        <label>Longitude:</label><input type="text" name="lon" value="{LONGITUDE}">
        <label>Latitude:</label><input type="text" name="lat" value="{LATITUDE}">
        
        <table class="tiny-table">
          <tbody>
            <tr>
              <td>Vancouver BC:</td><td class="num">-123.1207,</td><td class="num">49.2827</td>
              <td>Seattle WA:</td><td class="num">-122.3321,</td><td class="num">47.6062</td>
            </tr>
            <tr>
              <td>San Francisco CA:</td><td class="num">-122.4194,</td><td class="num">37.7749</td>
              <td>New York NY:</td><td class="num">-74.0060,</td><td class="num">40.7128</td>
            </tr>
            <tr>
              <td>London UK:</td><td class="num">-0.1278,</td><td class="num">51.5074</td>
              <td>Tokyo JP:</td><td class="num">139.6917,</td><td class="num">35.6895</td>
            </tr>
            <tr>
              <td>Sydney AU:</td><td class="num">151.2093,</td><td class="num">-33.8688</td>
              <td>Paris FR:</td><td class="num">2.3522,</td><td class="num">48.8566</td>
            </tr>
            <tr>
              <td>Beijing CN:</td><td class="num">116.4074,</td><td class="num">39.9042</td>
              <td>Kyiv UA:</td><td class="num">30.5234,</td><td class="num">50.4501</td>
            </tr>
          </tbody>
        </table>

        <label>Units:</label>
        <select id="units" name="units">
          <option value="metric" {"selected" if UNITS == "metric" else ""}>Metric</option>
          <option value="imperial" {"selected" if UNITS == "imperial" else ""}>Imperial</option>
        </select>

        <label>Interval minutes (15-60):</label>
        <select id="interval" name="interval"></select>

        <label>Days of forecast (2-5):</label>
        <div class = "tiny">
        For n-day forecasts, how many days are listed?<br>
        </div>
        <select id="n_day_forecast" name="n_day_forecast"></select>

        <div class="tiny">
        <br>openmeteo polls and displays are done between Starting hour and Ending hour<br>
        </div>
        <label>Starting Hour (0-23):</label>

        <select id="start_hour" name="start_hour"></select>

        <label>Ending Hour (0-23):</label>
        <select id="end_hour" name="end_hour"></select>

        <input type="submit" value="Save Changes">
      </form>
    </div>

    <script>
      const initialA = {START_HOUR};
      const initialB = {END_HOUR};
      const initialInterval = {QUERY_INTERVAL_MINUTES};
      const initialNDayForecast = {N_DAY_FORECAST};

      const A = document.getElementById('start_hour');
      const B = document.getElementById('end_hour');
      const interval = document.getElementById('interval');
      const n_day_forecast = document.getElementById('n_day_forecast');
      
      function clampMinToMax(n, min, max) {{
        n = Number(n);
        if (!Number.isFinite(n)) return min;
        n = Math.floor(n);
        if (n < min) return min;
        if (n > max) return max;
        return n;
      }}

      function buildSelect(selectEl, min_val, max_val) {{
        selectEl.innerHTML = '';
        for (let i = min_val; i <= max_val; i++) {{
          const opt = document.createElement('option');
          opt.value = String(i);
          opt.textContent = String(i);
          selectEl.appendChild(opt);
        }}
      }}

      function enforceMutualExclusion() {{
        const aVal = A.value;
        const bVal = B.value;

        for (let i = 0; i <= 23; i++) {{
          const v = String(i);
          const optB = B.querySelector('option[value="' + v + '"]');
          const optA = A.querySelector('option[value="' + v + '"]');
          if (optB) optB.disabled = (v === aVal);
          if (optA) optA.disabled = (v === bVal);
        }}

        if (B.querySelector('option[value="' + B.value + '"]')?.disabled) {{
          for (let i = 0; i <= 23; i++) {{
            const v = String(i);
            if (v !== A.value) {{ B.value = v; break; }}
          }}
        }}
        if (A.querySelector('option[value="' + A.value + '"]')?.disabled) {{
          for (let i = 0; i <= 23; i++) {{
            const v = String(i);
            if (v !== B.value) {{ A.value = v; break; }}
          }}
        }}
      }}

      buildSelect(A, 0, 23);
      buildSelect(B, 0, 23);
      buildSelect(interval, 15, 60);
      buildSelect(n_day_forecast, 2, 5);

      // init values with clamping
      let a0 = clampMinToMax(initialA,0,23);
      let b0 = clampMinToMax(initialB,0,23);

      let interval0 = clampMinToMax(initialInterval,15,60);
      interval.value = String(interval0);

      let n_day_forecast0 = clampMinToMax(initialNDayForecast,2,5);
      n_day_forecast.value = String(n_day_forecast0);

      if (a0 === b0) {{
        for (let i = 0; i <= 23; i++) {{
          if (i !== a0) {{ b0 = i; break; }}
        }}
      }}

      A.value = String(a0);
      B.value = String(b0);

      enforceMutualExclusion();
      A.addEventListener('change', enforceMutualExclusion);
      B.addEventListener('change', enforceMutualExclusion);
    </script>
  </body>
  </html>"""

async def handle_client(reader, writer):
    """
    Handle an incoming client connection, process the HTTP request, and send the appropriate response.
    
    This function reads the request line and headers, processes GET requests to update configuration settings,
    and sends back an HTML response or a redirect as needed. It also manages the connection lifecycle, ensuring
    that resources are cleaned up properly after handling the request.

    args:
        reader: An asyncio StreamReader object for reading data from the client.
        writer: An asyncio StreamWriter object for sending data to the client.

    Returns:
        None
    """
    log_debug("[main] handle_client()")
    log_debug("[Web Server] Connection detected! Reading request stream...")
    global settings_values_changed, termination_flag, gc
    try:
        request_line = await reader.readline()
        if not request_line:
            return

        # Exhaust incoming HTTP headers to free up hardware memory
        while termination_flag == False:
            line = await reader.readline()
            if line == b'\r\n' or line == b'\n' or not line:
                break

        request = request_line.decode('utf-8')
        method, url, _ = request.split(' ', 2)
        
        if method == "GET" and "/config" in url:
            log_debug("***\n\t\t\tProcessing returned data\n***")
            if "?" in url:
                query = url.split("?")[1]
                old_params = {}
                for k,v in settings.items():
                    old_params[k] = v

                params = query.split("&")
                for param in params:
                    kv = param.split("=")
                    if len(kv) == 2:
                        key, val = kv[0], kv[1]
                        
                        # MicroPython safety: wrap conversions in try/except 
                        # so partial/malformed strings don't crash the loop
                        try:
                            if key == "lat":
                                float_val = float(val)
                                # Check if the difference is more than a tiny rounding threshold (0.001)
                                old_val = old_params.get("LATITUDE", 0.0)
                                diff = abs(float_val - old_val)
                                log_debug(f"Latitude - Old value: {old_val}, New value: {float_val}, diff: {diff}")
                                if diff > 0.001:
                                    settings_values_changed = True
                                    settings["LATITUDE"] = float_val                            
                            elif key == "lon":
                                float_val = float(val)
                                old_val = old_params.get("LONGITUDE", 0.0)
                                diff = abs(float_val - old_val)
                                log_debug(f"Longitude: Old value: {old_val}, New value: {float_val}, diff: {diff}")
                                if diff > 0.001:
                                    settings_values_changed = True
                                    settings["LONGITUDE"] = float_val
                            elif key == "interval":
                                int_val = int(val)
                                if int_val != old_params.get("QUERY_INTERVAL_MINUTES"):
                                    settings_values_changed = True
                                    settings["QUERY_INTERVAL_MINUTES"] = int_val
                            elif key == "start_hour":
                                int_val = int(val)
                                if int_val != old_params.get("START_HOUR"):
                                    settings_values_changed = True
                                    settings["START_HOUR"] = int_val
                            elif key == "end_hour":
                                int_val = int(val)
                                if int_val != old_params.get("END_HOUR"):
                                    settings_values_changed = True
                                    settings["END_HOUR"] = int_val
                            elif key == "n_day_forecast":
                                int_val = int(val)
                                if int_val != old_params.get("N_DAY_FORECAST"):
                                    settings_values_changed = True
                                    settings["N_DAY_FORECAST"] = int_val
                            elif key == "units":
                                if val != old_params.get("UNITS"):
                                    settings_values_changed = True
                                    settings["UNITS"] = val

                        except (ValueError, TypeError) as ex:
                            log_debug(f"[Web Server] Form value parsing error on {key}={val}: {ex}")

                # Save the global structure (if updated) directly to config.json 
                if settings_values_changed:
                    await save_settings_async(settings)
                    log_debug(f"[Web Server] Live config updated and written: {settings}")

            # Send the redirect response back to the client browser
            writer.write("HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n".encode('utf-8'))
            await writer.drain()

            # Recycle streams cleanly for standalone deployment
            writer.close()
            await writer.wait_closed()
            
            gc.collect()
            await asyncio.sleep_ms(250)
            return 

        # Extract values from state registry
        LATITUDE = settings.get("LATITUDE", 0.0)
        LONGITUDE = settings.get("LONGITUDE", 0.0)
        QUERY_INTERVAL_MINUTES = settings.get("QUERY_INTERVAL_MINUTES", 15)

        # 1. Prepare and render the layout
        html_str = render_html(settings)
        response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: {}\r\n\r\n{}".format(len(html_str), html_str)
        
        try:
            # 2. Fully stream the payload to the browser
            writer.write(response.encode('utf-8'))
            await writer.drain()
        except Exception as e:
            print("[Web Server Error]:", e)
        finally:
            # 3. Completely shut down and tear down the inbound connection channel
            writer.close()
            await writer.wait_closed()
            print("[Web Server] Connection handled and socket closed.")

    except Exception as top_level_err:
        # ATTACHED: Handles any generic connection drops or socket stream reading failure errors
        log_debug(f"[Web Server] Top level connection error: {top_level_err}")
    finally:
        # ATTACHED: Ensures that even if reading the request lines crumbles midway, 
        # the client socket can't hang stuck in the event loop pipeline.
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

    # Force immediate collection of the massive html_str variable allocations
    gc.collect() 

    # Give the network stack a micro-window (e.g., 100-250ms) to clear local TCP states
    await asyncio.sleep_ms(250)

async def supervisor_task():
    """Watches the global termination flag and kills the loop if a task raises it."""
    global termination_flag
    while not termination_flag:
        await asyncio.sleep_ms(200)  # Check 5 times a second
    
    log_debug("[Supervisor] Termination semaphore detected! Stopping event loop...")
    loop = asyncio.get_event_loop()
    loop.stop()  # Forces loop.run_forever() inside main() to break immediately

async def main():
    global connected, termination_flag
    log_debug("[main] main()")
    try:
        settings = await load_settings_async()
        local_hhmm = initialize()
        # FORCE A DIAGNOSTIC PRINT TO TERMINAL
        log_debug(f"Raw State Content: {settings}")
    except KeyboardInterrupt:
        log_debug("[main]Program stopped by user. Exiting gracefully.")
        termination_flag = True
    except RuntimeError as e:
        log_debug(f"[main] Runtime error: {e}. Exiting.")
        df.presto_errors(f"[main] {e}")
    except Exception as e:
        log_debug(f"[main]An unexpected error occurred: {e}. Exiting.")
        df.presto_errors(f"[main] {e}")

    # set up the web handling as a co-routine
    server = await asyncio.start_server(handle_client, "0.0.0.0", 80)
    log_debug("[main] main(): Web server started on port 80...")

    # set up the weather polling task
    log_debug("[main] main(): Starting background loops...")
    try:
        await asyncio.gather(
            weather_loop_task(),
            supervisor_task()
        )
        log_debug("Web server and supervisor implemented.")
    except KeyboardInterrupt:
        log_debug("[main] Program stopped by user. Exiting gracefully.")
        termination_flag = True
    except Exception as e:
        log_debug(f"An unexpected error occurred: {e}. Exiting.")
    finally:
        server.close()
        await server.wait_closed()

if __name__ == "__main__":
    try:
        # Let asyncio run your app normally
        asyncio.run(main())
        
    except KeyboardInterrupt:
        # MicroPython will intercept the stop button here!
        print("\n[System] Program stopped by user. Cleaning up...")
        termination_flag = True
        
        # MicroPython specific: clear any pending hardware states if needed
        # (e.g., turning off pins, closing open display files, etc.)
        
    except Exception as e:
        print(f"[System] Fatal unhandled crash: {e}")
