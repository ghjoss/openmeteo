from openmeteo_api_data import LONGITUDE, LATITUDE, UNITS, TIMEZONE
from control import DEBUG, FORECAST_HOURS, N_DAY_FORECAST, log_debug
import display_functions as df
import requests
import gc

def init_provider():
    global forecast_anchors, forecast_hours

    global WEATHER_CODES_FULL, WEATHER_GROUPS
    global header_pen, data_pen, alert_pen, background_pen, date_pen

    WEATHER_CODES_FULL = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }

    WEATHER_GROUPS = {
        (0,): "Clear",
        (1, 2, 3): "Cloudy",
        (45, 48): "Foggy",
        (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82): "Rainy",
        (71, 73, 75, 77, 85, 86): "Snowy",
        (95, 96, 99): "Stormy" # thunderstorm
    }
     
    forecast_anchors = [35, 105, 145, 187, 230]

    # validate and set forecast hours
    forecast_hours = FORECAST_HOURS

    log_debug("Initializing weather provider...")
    header_pen = df.new_pen("_SlateBlue")
    data_pen = df.new_pen("_PaleTurquoise") # "_Cornsilk","_Cyan","_Gray","_DarkSlateGray"
    alert_pen = df.new_pen("_Coral")
    background_pen = df.new_pen("_Black") #"_Cornsilk")
    date_pen = df.new_pen("_RoyalBlue")
 
    df.cls()
def get_max_temp(data,start_idx,end_idx):

    # iterate through the next passed range of hours to determine the
    # highest temperature in the range.
    maxTemp =-9999
    maxidx = -1
    for i in range(start_idx, end_idx):
        temp = data["hourly"]["temperature_2m"][i]
        if temp > maxTemp:
            maxTemp = temp
            maxidx = i
    return maxTemp, maxidx

def split_at_forty(text: str):
    # Check if the string actually exceeds the 40-character limit
    if len(text) > 40:
        # Slice the string to the first 40 characters
        first_part = text[:40]
        
        if " " in first_part:
            # Find the last space within those 40 characters and split once
            left, right = first_part.rsplit(" ", 1)
            
            # The second piece is the remainder of the 40 chars + everything after index 40
            second_part = right + text[40:]
            return [left, second_part]
        
        # Fallback: If there are NO spaces in the first 40 characters, 
        # we have to do a hard cut at 40 to avoid breaking the logic.
        return [f"{text[:40]}-", text[40:]] # append "-" continuation char to first part
        
    # If it's 40 characters or fewer, leave it as a single piece
    return [text]

def format_current_weather_data(data, city):
    log_debug("format_current_weather_data()")

    global header_pen, data_pen, alert_pen, background_pen, date_pen

    current = data["current"]
    hourly = data["hourly"]

    anchors_current = [[35], [105], [170], [235]]
 
    max_temp, max_idx = get_max_temp(data,0,24)
    max_temp_label = "Max Temp:"
    max_date_time_text = hourly["time"][max_idx] # e.g. "yyyy-mo-ddThh:mm"
    maxTime = max_date_time_text.split("T")[1]

    current_temp = current["temperature_2m"]
    current_apparent_temp = current["apparent_temperature"]
    current_precipitation = current["precipitation"]
    current_rain = current["rain"]  
    current_showers = current["showers"]
    current_snow = current["snowfall"]
    current_cloud_cover = current["cloud_cover"]

    temp_units = data["current_units"]["temperature_2m"]
    precipitation_units = data["current_units"]["precipitation"]
    cloud_cover_units = data["current_units"]["cloud_cover"]

    current_wind = current["wind_speed_10m"]
    wind_speed_units = data["current_units"]["wind_speed_10m"]

    current_weather_code = current["weather_code"]
    current_rel_humidity = current["relative_humidity_2m"]
    rel_hum_units = data["current_units"]["relative_humidity_2m"]

    current_uv_index = data["current"]["uv_index"]
 
    df.cls()
    forecast_time = current["time"].split("T")[1]
    line = [f"{city} Weather: as of {forecast_time}"]
    log_debug(line[0])
    df.draw_vector_row(line,15,header_pen,anchors=[])

    y_row = 45
    log_debug(f"Current temp:{current_temp}")
    line = ["Current temp:"]
    df.draw_vector_row(line,y_row,header_pen,anchors=anchors_current[1])
    line = [f"{current_temp:02.1f} {temp_units}"]
    df.draw_vector_row(line,y_row,data_pen,anchors=anchors_current[2])

    row_increment_value = 15

    y_row += row_increment_value
    log_debug(f"Feels like: {current_apparent_temp}")
    line = ["Feels like:"]
    df.draw_vector_row(line,y_row,header_pen,anchors=anchors_current[1])
    line = [f"{current_apparent_temp:02.1f} {temp_units}"]
    df.draw_vector_row(line,y_row,data_pen,anchors=anchors_current[2])
    
    y_row += row_increment_value
    line = [max_temp_label]
    df.draw_vector_row(line,y_row,header_pen,anchors=anchors_current[1])
    line = [f"{max_temp:02.1f} {temp_units}"]
    df.draw_vector_row(line,y_row,alert_pen,anchors=anchors_current[2])
    line = [f"@ {maxTime}"]
    df.draw_vector_row(line,y_row,header_pen,anchors=anchors_current[3])


    y_row += row_increment_value
    log_debug(f"Wind speed:{current_wind}")
    line = ["Wind speed:"]
    df.draw_vector_row(line,y_row,header_pen,anchors=anchors_current[1])
    line = [f"{current_wind:02.1f} {wind_speed_units}"]
    df.draw_vector_row(line,y_row,data_pen,anchors=anchors_current[2])

    y_row += row_increment_value
    log_debug(f"UV Index: {current_uv_index}")
    line = ["UV Index:"]
    df.draw_vector_row(line,y_row,header_pen,anchors=anchors_current[1])
    line = [f"{current_uv_index:02.2f}"]
    df.draw_vector_row(line,y_row,data_pen,anchors=anchors_current[2])

    y_row += row_increment_value
    log_debug(f"Rel. Hum. {current_rel_humidity}")
    line = ["Humidity:"]
    df.draw_vector_row(line,y_row,header_pen,anchors=anchors_current[1])
    line = [f"{current_rel_humidity:02.1f} {rel_hum_units}"]
    df.draw_vector_row(line,y_row,data_pen,anchors=anchors_current[2])

    y_row += row_increment_value
    log_debug(f"Cloud cover: {current_cloud_cover} {cloud_cover_units}")
    line = ["Cloud cover:"]
    df.draw_vector_row(line,y_row,header_pen,anchors=anchors_current[1])
    line = [f"{current_cloud_cover:02.1f} {cloud_cover_units}"]
    df.draw_vector_row(line,y_row,data_pen,anchors=anchors_current[2])

    y_row += row_increment_value
    log_debug(f"Precipitation: {current_precipitation}")
    line = ["Precipitation:"]
    df.draw_vector_row(line,y_row,header_pen,anchors=anchors_current[1])
    line = [f"{current_precipitation:02.3f} {precipitation_units[:2]}"]
    df.draw_vector_row(line,y_row,data_pen,anchors=anchors_current[2])

    y_row += row_increment_value
    if current_precipitation > 0:
        log_debug(f"  Rain: {current_rain}  {precipitation_units[:2]}"
              f"Showers: {current_showers}  {precipitation_units[:2]}"
              f"  Snowfall: {current_snow}  {precipitation_units[:2]}")
        line = ["Rain:"]
        df.draw_vector_row(line,y_row,header_pen,anchors=anchors_current[0])
        line = [f"{current_rain} {precipitation_units[:2]}"]
        df.draw_vector_row(line,y_row,data_pen,anchors=anchors_current[1])
        line = ["Showers:"]
        df.draw_vector_row(line,y_row,header_pen,anchors=anchors_current[2])
        line = [f"{current_showers} {precipitation_units[:2]}"]
        df.draw_vector_row(line,y_row,data_pen,anchors=anchors_current[3])
        y_row += row_increment_value
        line = ["Snow:"]
        df.draw_vector_row(line,y_row,header_pen,anchors=anchors_current[0])
        line = [f"{current_snow} {precipitation_units[:2]}"]
        df.draw_vector_row(line,y_row,data_pen,anchors=anchors_current[1])
        
    y_row += int(row_increment_value * 1.75)
    weather_text = WEATHER_CODES_FULL[current_weather_code]
    log_debug(f"Weather: {weather_text} (code={current_weather_code})")
    # The longest weather code: "Thunderstorm with slight hail" is 29 chars.
    # but for insurance, split lines longer than 40 chars at the last space to
    # print those longer lines on two lines (assumes not longer than 80)
    weather_list = split_at_forty(weather_text)
    line = weather_list[0]
    if len(weather_list) > 1:
        line = f"{line}\n{weather_list[1]}"
    
    df.draw_vector_row([line],y_row,data_pen,anchors=[])
    
#    Line measuring tool
#    line = ["____0____1____1____2____2____3____3____4____4____5____5____6____6"]
#    df.draw_vector_row(line,y_row,value_pen,anchors=[])
#    line = ["____5____0____5____0____5____0____5____0____5____0____5____0____5"]
#    y_row += 10
#    df.draw_vector_row(line,y_row,value_pen,anchors=[])
    df.refresh()
    log_debug("...end format_current_weather_data()")


def format_precipitation_data(data):
    log_debug("format_precipitation_data()")
    global forecast_anchors
    global forecast_hours
    global header_pen, data_pen, alert_pen, background_pen, date_pen
    
    # starting row of text
    row_y = 20

    current = data["current"]
    hourly = data["hourly"]

    # Get the current hour string from the API (e.g., "2026-05-12T07:00")
    # We use [:13] + ":00" to ensure it matches the top-of-hour format in the hourly list
    current_date_time = current["time"]
    current_hour_api = current_date_time[:13] + ":00"
    forecast_time = current_date_time.split("T")[1]
   

    # Find where this hour exists in the hourly list
    try:
        start_idx = hourly["time"].index(current_hour_api)
    except ValueError:
        # Fallback to 0 if for some reason the current hour isn't in the data
        start_idx = 0
    
    # Format and print the header rows for the forecast data.
    date_time_text = hourly["time"][start_idx] # e.g. "yyyy-mo-ddThh:mm"
    date_text = date_time_text.split("T")[0] # "yyyy-mo-dd"

    msg = [f"Precipitation forecast as of {forecast_time}"]
    df.draw_vector_row(msg, row_y, date_pen, anchors=[])
    row_y += df.row_step
    line = ["","Temp.","Amt.","Rel.","Prob."]
    df.draw_vector_row(line,row_y,header_pen,anchors=forecast_anchors)
    row_y += df.row_step
    line=["",f"({data["current_units"]["temperature_2m"]})",f"({data["current_units"]["precipitation"]})","Hum","precip."]
    df.draw_vector_row(line,row_y,header_pen,anchors=forecast_anchors)
    row_y += 5
    df.draw_vector_row(["_" * 45], row_y, header_pen,anchors=[])
 
    row_y += df.row_step

    # iterate through the next N hours of data starting from the current hour to determine the
    # highest temperature in the forecast period. We will use this to highlight the row with the highest temp.
    maxTemp, maxidx = get_max_temp(data,start_idx,start_idx + forecast_hours)

    # Now iterate through the data again to print it out, this time highlighting the row with the highest temperature.
    date_text_old = ""
    for i in range(start_idx, start_idx + forecast_hours):
        date_time_text = hourly["time"][i] # e.g. "yyyy-mo-ddThh:mm"
        date_text = date_time_text.split("T")[0] # "yyyy-mo-dd"
        if date_text != date_text_old:
            if date_text_old != "":
                row_y += int(df.row_step * .5)
            date_display = f"{date_text}"    
            df.draw_vector_row([date_display], row_y, date_pen)    

            row_y += df.row_step
            date_text_old = date_text

        # Extract just the hour
        time_text = date_time_text.split("T")[1] # "hh:mm"

        temp = hourly["temperature_2m"][i]
        apparent_temp = hourly["apparent_temperature"][i]
        temp = f"{temp:02.1f}({apparent_temp:02.1f})"
        precipitation = hourly["precipitation"][i]
        precipitation_probability = hourly["precipitation_probability"][i]
        rel_humidity = hourly["relative_humidity_2m"][i]

        line = [time_text, f"{temp}", f"{precipitation:2.3f}", f"{rel_humidity:3.0f}%", f"{precipitation_probability:2.1f}"]

        line_pen = data_pen
        #highlight the highest temp in the request
        if i == maxidx:
            line_pen = alert_pen

        df.draw_vector_row(line, row_y, line_pen, anchors=forecast_anchors)
        row_y += df.row_step
        log_debug(f"{time_text} | {temp}({apparent_temp}) {data["current_units"]["temperature_2m"]} | {precipitation} {data["current_units"]["precipitation"]} | {rel_humidity}% | {precipitation_probability}%")

    # After drawing all the lines, refresh the display to show the new data
    df.refresh()
    log_debug("...end format_precipitation_data()")

def consolidate_weather_codes(code):
    for c in WEATHER_GROUPS:
        if code in c:
            return WEATHER_GROUPS[c]
    return f"--- weather code {code} ---"

def format_forecast_data(data):
    log_debug("format_forecast_data()")
    global forecast_anchors
    global forecast_hours

    global header_pen, data_pen, alert_pen, background_pen, date_pen
    
    # starting row of text
    row_y = 20

    current = data["current"]
    hourly = data["hourly"]
#    daily = data["daily"]

    # Get the current hour string from the API (e.g., "2026-05-12T07:00")
    # We use [:13] + ":00" to ensure it matches the top-of-hour format in the hourly list
    current_date_time = current["time"]
    current_hour_api = current_date_time[:13] + ":00"
    forecast_time = current_date_time.split("T")[1]
   

    # Find where this hour exists in the hourly list
    try:
        start_idx = hourly["time"].index(current_hour_api)
    except ValueError:
        # Fallback to 0 if for some reason the current hour isn't in the data
        start_idx = 0
    
    temperature_label = data["hourly_units"]["temperature_2m"]
    wind_speed_label = data["hourly_units"]["wind_speed_10m"]
    uv_label = data["hourly_units"]["uv_index"]

    # iterate through the next N hours of data starting from the current hour, or as close to it as we can get with the data we have.
            # 1. Define where each column SHOULD end (Right Anchor)
    SCALE = df.default_scale

    # Format and print the header rows for the forecast data.
    date_time_text = hourly["time"][start_idx] # e.g. "yyyy-mo-ddThh:mm"
    date_text = date_time_text.split("T")[0] # "yyyy-mo-dd"

    msg = [f"Weather forecast as of {forecast_time}"]
    df.draw_vector_row(msg, row_y, date_pen, anchors=[])
    row_y += df.row_step
    line = ["","Temp","Wind","UV","Desc"]
    df.draw_vector_row(line,row_y,header_pen,anchors=forecast_anchors)
    row_y += df.row_step
    line=["",f"({temperature_label})",f"{wind_speed_label}","Index",""]
    df.draw_vector_row(line,row_y,header_pen,anchors=forecast_anchors)
    row_y += 5
    df.draw_vector_row(["_" * 45], row_y, header_pen,anchors=[])
    row_y += df.row_step

    # iterate through the next N hours of data starting from the current hour to determine the
    # highest temperature in the forecast period. We will use this to highlight the row with the highest temp.
    maxTemp, maxidx = get_max_temp(data,start_idx,start_idx + forecast_hours)

    # Now iterate through the data again to print it out, this time highlighting the row with the highest temperature.
    date_text_old = ""
    for i in range(start_idx, start_idx + forecast_hours):
        date_time_text = hourly["time"][i] # e.g. "yyyy-mo-ddThh:mm"
        date_text = date_time_text.split("T")[0] # "yyyy-mo-dd"
        if date_text != date_text_old:
            if date_text_old != "":
                row_y += int(df.row_step * .5)
            date_display = f"{date_text}"    
            df.draw_vector_row([date_display], row_y, date_pen)    

            row_y += df.row_step
            date_text_old = date_text

        # Extract just the hour
        time_text = date_time_text.split("T")[1] # "hh:mm"

        temp = hourly["temperature_2m"][i]
        apparent_temp = hourly["apparent_temperature"][i]
        temp = f"{temp:02.1f}({apparent_temp:02.1f})"
        weather_code = hourly["weather_code"][i]

        wind_speed = hourly["wind_speed_10m"][i]
        uv = hourly["uv_index"][i]

        if uv == None:
            uv = "n/a"
        else:
            uv = f"{uv:2.1f}"

        line = [time_text, f"{temp}", f"{wind_speed:4.1f}", uv, f"{consolidate_weather_codes(weather_code)}"]

        line_pen = data_pen
        #highlight the highest temp in the request
        if i == maxidx:
            line_pen = alert_pen

        df.draw_vector_row(line, row_y, line_pen, anchors=forecast_anchors)
        row_y += df.row_step
        log_debug(f"{time_text} | {temp}{temperature_label} | {wind_speed}{wind_speed_label} | uv index: {uv} | {consolidate_weather_codes(weather_code)}")

    # After drawing all the lines, refresh the display to show the new data
    df.refresh()
    log_debug("...end format_forecast_data()")

def format_N_day_forecast_data(data,N):
    global forecast_anchors
    anchored = True
    log_debug("format_N_day_forecast_data()")
    N_day_forecast_anchors = [75, 145, 185, 230]

    global header_pen, data_pen, alert_pen, background_pen, date_pen
    
    # starting row of text
    row_y = 20

    daily = data["daily"]
    daily_units = data["daily_units"]

    temperature_label = daily_units["temperature_2m_max"]
    wind_speed_label = daily_units["wind_speed_10m_max"]
    precip_units = daily_units["precipitation_sum"]

    # Format and print the header rows for the forecast data.
    line = [f"{N} day forecast"]
    df.draw_vector_row(line, row_y, date_pen, anchors=[])
    row_y += df.row_step

    h1 = ""
    h2 = "Max/Min"
    h3 = "Max"
    h4 = "Total"
    if anchored:
        hdr = [h1,h2,h3,h4]
        df.draw_vector_row(hdr,row_y,header_pen,anchors=N_day_forecast_anchors)
    else:
        hdr = [f"{h1:12s}{h2:<12s}{h3:<7s}{h4:>6s}"]
        df.draw_vector_row(hdr,row_y,header_pen,anchors=[])

    row_y += df.row_step

    h1 = "Date"
    h2 = "Temp."
    h3 = "Wind"
    h4 = "Precip"
    if anchored:
        hdr = [h1,h2,h3,h4]
        df.draw_vector_row(hdr,row_y,header_pen,anchors=N_day_forecast_anchors)
    else:
        hdr = [f"{h1:12s}{h2:<12s}{h3:<7s}{h4:>6s}"]
        df.draw_vector_row(hdr,row_y,header_pen,anchors=[])
    row_y += df.row_step
    h1 = ""
    h2 = f"{temperature_label}"
    h3 = f"{wind_speed_label}"
    h4 = f"{precip_units}"
    if anchored:
        hdr = [h1,h2,h3,h4]
        df.draw_vector_row(hdr,row_y,header_pen,anchors=N_day_forecast_anchors)
    else:
        hdr = [f"{h1:12s}{h2:<12s}{h3:<7s}{h4:>6s}"]
        df.draw_vector_row(hdr,row_y,header_pen,anchors=[])
    row_y += 5
    
    df.draw_vector_row(["_" * 45], row_y, header_pen,anchors=[])
    row_y += df.row_step
    row_y += df.row_step

    for i in range(0, len(daily["time"])):
        date_time_text = daily["time"][i]
        date_text = date_time_text.split("T")[0] # yyyy-mo-dd

        max_temp = daily["temperature_2m_max"][i]
        min_temp = daily["temperature_2m_min"][i]
        max_wind = daily["wind_speed_10m_max"][i]


        total_precip = daily["precipitation_sum"][i]
        h1 = f"{date_text}"
        h2 = f"{max_temp:02.1f}/{min_temp:02.1f}"
        h3 = f"{max_wind:4.1f}"
        h4 = f"{total_precip:2.3f}"
        if anchored:
            line = [h1,h2,h3,h4]
            df.draw_vector_row(line,row_y,data_pen,anchors=N_day_forecast_anchors)
        else:
            line = [f"{h1:12s}{h2:<12s}{h3:<7s}{h4:>6s}"]
            df.draw_vector_row(line, row_y, data_pen, anchors=[])

        row_y += df.row_step
        log_debug(line)

    try:
        df.refresh()
    except Exception as e:
        log_debug(f"Error refreshing display: {e}")

    log_debug("...end format_N_day_forecast_data()")

def get_forecast_data(Days=3):
    
    if UNITS == "imperial":
        temperature_unit = "fahrenheit"
        wind_speed_unit = "mph"
        precipitation_unit = "inch"
    else:
        temperature_unit = "celsius"
        wind_speed_unit = "ms"
        precipitation_unit = "millimeter"

    # &hourly= temperature_2m,apparent_temperature,rain,showers,snowfall,
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}"
        f"&hourly=temperature_2m,apparent_temperature,precipitation_probability,precipitation,"
        f"rain,showers,snowfall,weather_code,cloud_cover,wind_speed_10m,relative_humidity_2m,uv_index"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,showers,snowfall,weather_code,cloud_cover,wind_speed_10m,uv_index"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max"
        f"&timezone=auto&forecast_days={Days}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&models=best_match"
		f"&wind_speed_unit={wind_speed_unit}&temperature_unit={temperature_unit}&precipitation_unit={precipitation_unit}"
        )
    log_debug(url)
    response = None
    try:
        gc.collect() # Clean RAM before the request
        response = requests.get(url)
        data = response.json()
        log_debug(data)
        return data
    except Exception as e:
        log_debug(f"Meteo Error: {e}")
        return None
    finally:
        if response:
            response.close()
        gc.collect()
