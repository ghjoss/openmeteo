import time
from control import DEBUG, QUERY_INTERVAL, START_HOUR, END_HOUR, N_DAY_FORECAST, log_debug
from router import OPEN_STREETMAP_AGENT
from openmeteo_api_data import LONGITUDE, LATITUDE
import display_functions as df
from network_access import wifi_connect
from presto import Presto
import picovector
import openmeteo
import ntptime
import urequests as requests
import random
import openmeteo_chart

def initialize():
    """
    Initialize the weather provider. 
    This function sets up the necessary hardware and software components, including connecting to WiFi, initializing the Presto display, 
    and setting up the weather API provider. It also validates the query interval and forecast hours based on the provided configuration.

    Returns:
        None
    """
    # hardware globals
    global presto, display, vector, brightness


    # software globals
    global connected, query_interval, now, city
    query_interval = QUERY_INTERVAL

    global current_view_state, FORECAST_VIEW, CURRENT_WEATHER_VIEW, PRECIPITATION_VIEW, N_DAYS_FORECAST_VIEW
    global FORECAST_CHART_VIEW, PRECIPITATION_CHART_VIEW,VIEW_STATES
    global START_HOUR, END_HOUR, N_DAY_FORECAST
    
    CURRENT_WEATHER_VIEW = 3
    PRECIPITATION_VIEW = 2
    N_DAYS_FORECAST_VIEW = 0
    FORECAST_VIEW = 4
    FORECAST_CHART_VIEW = 5
    PRECIPITATION_CHART_VIEW = 1
    VIEW_STATES = 6
    log_debug("Starting...")

    # connect to WiFi
    log_debug("Connecting to WiFi...")
    connected = False
    netLan = wifi_connect()

    if netLan is None:
        raise RuntimeError("Unable to connect to WiFi network. Program terminating.")

    log_debug(f"...connected! IP: {netLan.ifconfig()[0]}")

    connected = True
    
    # use longitude and latitude to get the city name
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={LATITUDE}&lon={LONGITUDE}"
    headers = {"User-Agent": f"{OPEN_STREETMAP_AGENT}"}
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

    log_debug("Presto initialization...")
    presto = Presto()
    display = presto.display

    display.set_pen(display.create_pen(0,0,0))
    display.clear()

    vector = picovector.PicoVector(display)
    vector.set_antialiasing(picovector.ANTIALIAS_BEST)
    log_debug("...Presto initialized, call display_functions.init_provider...)")
    
    # get UTC offset seconds for the location, which will be used to determine when to sleep the display
    global UTC_OFFSET_SECONDS
    try:
        UTC_OFFSET_SECONDS = 0
        url = f"https://timeapi.io/api/timezone/coordinate?latitude={LATITUDE}&longitude={LONGITUDE}"
        res = requests.get(url,timeout=5)
        data = res.json()
        UTC_OFFSET_SECONDS = data["currentUtcOffset"]["seconds"]
    except Exception as e:
        log_debug(f"Unable to get UTC offset seconds for the location, defaulting to 0. Error: {e}")

    df.init_provider(presto, rotational_shift=-15)
    #df.init_provider(presto, rotational_shift=-22,font="AdventPro-Black.af",scale=20)

    log_debug("...display provider initialized, call weatherapi.init_provider...)")
    openmeteo.init_provider()
    log_debug("...weather provider initialized")
    brightness = 0.3 # start out at ~1/3
    presto.set_backlight(brightness)
    presto.update()
    openmeteo_chart.init_provider(presto)

def responsive_wait(minutes, data, sleeping):
    """
    Wait for a specified number of minutes while allowing for responsive interruption.
    This function uses a loop with short sleep intervals to check for:
        o   Ctrl-C (KeyboardInterrupt) signal when running from an IDE for testing, 
            allowing the user to stop the program gracefully.
        o   A left or right swipe, changing the view mode among current weather, 
            a 1-8 hour forecast, and precipitation.
        o   If sleeping is True, the display is turned off. However, if the screen
            is touched, then the display is turned on for the duration of the wait
            and turned off by the caller.
    
    Args:
        minutes (int): The number of minutes to wait. This is converted to 
        millisecond timer ticks and checked every 20 milliseconds.
        sleeping: True or False. Invoked with True by caller if the
        current time is not between START_TIME and END_TIME
    Returns:
        None
    """
    global presto, current_view_state, brightness, city
    global N_DAY_FORECAST

 
    # swipe and touch control variables
    MIN_SWIPE_DISTANCE = 40   # pixels the finger must move to be considered a left-right swipe
    SWIPE_THRESHOLD = .4        # seconds a touch may last to still be only a tap and not a swipe
    touch_started = False
    start_time = 0

    # Use ticks_ms for better precision and less overhead than time.time()
    start_tick = time.ticks_ms()
    max_ticks = minutes * 60 * 1000

    # responsive_wait() is called every time the weather is updated. Trigger
    # a display of the data for the current view state by setting viewStateChanged 
    # to True
    viewStateChanged = True
    lcl_sleeping = sleeping

    log_debug(f"Waiting {minutes} min...")
    # The minutes to wait parameter has been converted to max_ticks.
    get_weather_once = True
    while time.ticks_diff(time.ticks_ms(), start_tick) < max_ticks:
        if not lcl_sleeping:
            if sleeping and get_weather_once: # if sleeping == True and lcl_sleeping == False:there was a touch, update weather
                get_weather_once = False
                data = get_forecast_with_retries(N_DAY_FORECAST)
            if viewStateChanged:
                df.cls()
                if current_view_state == FORECAST_VIEW:
                    openmeteo.format_forecast_data(data)
                elif current_view_state == CURRENT_WEATHER_VIEW:
                    openmeteo.format_current_weather_data(data, city)
                elif current_view_state == PRECIPITATION_VIEW:
                    openmeteo.format_precipitation_data(data)
                elif current_view_state == N_DAYS_FORECAST_VIEW:
                    openmeteo.format_N_day_forecast_data(data,N=N_DAY_FORECAST)
                elif current_view_state == FORECAST_CHART_VIEW:
                    openmeteo_chart.temp_wind_uv_charts(data)
                elif current_view_state == PRECIPITATION_CHART_VIEW:
                    openmeteo_chart.precipitation_charts(data)
                viewStateChanged = False

        presto.touch_poll()

        x, y, touched = presto.touch_a

        if touched:
            # Start tracking the swipe if it hasn't already started 
            if not touch_started:
                # and keep checking for swipes up-down left-right when touch released
                touch_started = True
                start_x = x
                start_y = y
                start_time = time.ticks_ms()
        else:
            # touch was released, check if a swipe was in progress
            if touch_started:
                end_x = x
                end_y = y
                dx = end_x - start_x
                adx = abs(dx)
                dy = end_y - start_y
                ady = abs(dy)
                elapsed = time.ticks_diff(time.ticks_ms(), start_time) / 1000 # ticks to seconds
                lcl_sleeping = False # whether a tap or swipe, wake up the display if it is sleeping

                if adx < MIN_SWIPE_DISTANCE and ady < MIN_SWIPE_DISTANCE and elapsed < SWIPE_THRESHOLD:
                    log_debug("Tap detected") 
                # check for swipe left,right
                elif adx >= ady: # horizontal swipes dominate
                    if dx > 0: # right
                        current_view_state = (current_view_state + 1) % VIEW_STATES
                        viewStateChanged = True
                        log_debug("Swiped right, switching view.")
                    else: # left
                        current_view_state = (current_view_state - 1) % VIEW_STATES
                        viewStateChanged = True
                        log_debug("Swiped left, switching view.")
                # if we have processed swipe left or right, do not
                # also process brightness change as it might be
                # an accidental vertical slant to the left-right swipe
                else:
                    # check for swipe up,down
                    if dy > 0: # down
                        log_debug("swiped down, brightness down...",end="")
                        level_change =-0.05
                    else: # up
                        level_change = 0.05
                        log_debug("swiped up, brightness up...",end="")
                    log_debug(f"level={brightness} ",end="")
                    brightness = df.set_backlight(brightness,level_change)
                    log_debug(f" new level {brightness}")
            # Reset the touch tracking
            touch_started = False    
        time.sleep_ms(20)
    return

def get_now_list():
    global UTC_OFFSET_SECONDS
    try:
        ntptime.settime()
        now = time.gmtime(time.time() + UTC_OFFSET_SECONDS)
        return [now[3],now[4]]
    except:
        return []

def in_range(cur_h: int, start_h: int, end_h: int) -> bool:
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
    if start_h == end_h:
        # Empty interval – nothing is inside it.
        # (If you prefer a full‑day interval, simply `return True` here.)
        return False

    # ---- interval check ---------------------------------------
    if start_h < end_h:                       # normal (no wrap‑around)
        return start_h <= cur_h < end_h
    else:                                     # wraps past midnight
        return cur_h >= start_h or cur_h < end_h

def get_forecast_with_retries(max_retries=6, initial_interval=400):
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
    global N_DAY_FORECAST
    interval = initial_interval
    for attempt in range(max_retries):
        data = openmeteo.get_forecast_data(N_DAY_FORECAST)
        if data is not None:
            return data
        else:
            log_debug(f"Attempt {attempt + 1} failed. Retrying in {interval} ms...")
            time.sleep_ms(interval)
            interval *= 2  # Exponential backoff

    raise RuntimeError("Unable to retrieve forecast data after multiple attempts.")

def main():
    try:
        initialize()
        sleeping = False
        global connected, query_interval, current_view_state, START_HOUR, END_HOUR
        data = None

        if connected:
            current_view_state = CURRENT_WEATHER_VIEW  #CURRENT_WEATHER_VIEW, FORECAST_VIEW, PRECIPITATION_VIEW
            while True:
                if not sleeping:
                    data = get_forecast_with_retries()
            
                now_list = get_now_list()
                log_debug(now_list)
                if len(now_list) > 0:
                    sleeping = not in_range(now_list[0], START_HOUR, END_HOUR)
                
                if sleeping:
                    df.cls()
                    df.set_backlight(0.0)
                
                responsive_wait(query_interval, data, sleeping)

    except KeyboardInterrupt:
        log_debug("Program stopped by user. Exiting gracefully.")
    except RuntimeError as e:
        log_debug(f"Runtime error: {e}. Exiting.")
        df.presto_errors(f"{e}")
    except Exception as e:
        log_debug(f"An unexpected error occurred: {e}. Exiting.")
        df.presto_errors(f"{e}")

if __name__ == "__main__":
    main()    
