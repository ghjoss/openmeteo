from pichart import Container, Chart, Card, TextCard, Located_Container
from control import log_debug, settings
import display_functions as df
import gc
import json
import asyncio
import time

def init_provider(main_presto, settings):
    global presto, display, WIDTH, HEIGHT

    log_debug("pichart_client_initialization")
    presto = main_presto
    display = presto.display
    WIDTH, HEIGHT = display.get_bounds()

    global chart_data_color_temp, chart_data_color_precip, chart_grid_color, chart_background_color
    chart_data_color_temp = df.translate_color(settings.get("CHART_DATA_COLOR","_Red"))
    chart_data_color_precip = df.translate_color(settings.get("CHART_DATA_COLOR_PRECIP","_Green"))
    chart_grid_color = df.translate_color(settings.get("CHART_GRID_COLOR","_LightGray"))
    chart_background_color = df.translate_color(settings.get("CHART_BACKGROUND_COLOR","_White"))

    global forecast_anchors

    global WEATHER_CODES_FULL, WEATHER_GROUPS
    global header_pen, data_pen, alert_pen, background_pen, date_pen
    log_debug("[openmeteo] init_provider()")

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

    log_debug("Initializing weather provider...")
    header_pen = df.new_pen("_SlateBlue")
    data_pen = df.new_pen("_PaleTurquoise") # "_Cornsilk","_Cyan","_Gray","_DarkSlateGray"
    alert_pen = df.new_pen("_Coral")
    background_pen = df.new_pen("_Black") #"_Cornsilk")
    date_pen = df.new_pen("_RoyalBlue")
 
    df.cls()

def split_at_forty(text: str):
    """ 
    Check if the string actually exceeds the 40-character limit
    If it does, split the string at the last space before the 40-character limit
    If there are no spaces, split at 40 characters and append a continuation character
    
    Args:
        text (str): The input string to be split.

    Returns:
        list: A list containing the split parts of the string.
    """
    log_debug("[openmeteo] split_at_forty()")
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
    """
    show the current weather conditions
    Args:
        data (dict): The weather data dictionary containing current and hourly weather information.
        city (str): The name of the city for which the weather data is being displayed.

    Returns:
        None    
    """
    log_debug("[openmeteo] format_current_weather_data()")
    df.cls()
    global header_pen, data_pen, alert_pen, background_pen, date_pen

    current = data["current"]
    hourly = data["hourly"]

    anchors_current = [[35], [105], [170], [235]]
 
    maxidx, maxtemp = max(enumerate(hourly["temperature_2m"][0:24]), key=lambda t: t[1])
    max_temp_label = "Max Temp:"
    max_date_time_text = hourly["time"][maxidx] # e.g. "yyyy-mo-ddThh:mm"
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
    line = [f"{city} Weather: as of {forecast_time} poll"]
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
    line = [f"{maxtemp:02.1f} {temp_units}"]
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

def get_start_idx(data):
    """ 
    Get the current hour string from the API (e.g., "2026-05-12T07:00")
    Use [:13] + ":00" to ensure it matches the top-of-hour format in the hourly list.
    Then find the offset of that time in the hourly list as the starting index (start_idx)
    for the next hours of forecast reporting.

    Args:
        data (dict): The weather data dictionary containing current and hourly weather information.
    Returns:
        tuple: A tuple containing the starting index (start_idx) and the forecast time string (forecast_time).
    """
    log_debug("[openmeteo] get_start_idx()")
    current = data["current"]
    hourly = data["hourly"]
    current_date_time = current["time"]
    current_hour_api = current_date_time[:13]+":00"
    forecast_time = current_date_time.split("T")[1]
    # Find where this hour exists in the hourly list
    try:
        start_idx = hourly["time"].index(current_hour_api)
    except ValueError:
        # Fallback to 0 if for some reason the current hour isn't in the data
        start_idx = 0
    return start_idx, forecast_time

def format_precipitation_chart(data, settings, container, start_idx, title, divider):
    """
    Format the precipitation chart based on the provided weather data and settings.

    Args:
        data (dict): The weather data dictionary containing current and hourly weather information.
        settings (dict): A dictionary containing the configuration settings.
        container (Located_Container): The container to which the chart will be added.
        start_idx (int): The starting index for the forecast data.
        title (str): The title for the precipitation chart.
        divider (int): The divider for determining the chart height.
    """
    log_debug("[openmeteo] format_precipitation_chart()")
    hourly = data["hourly"]
    hourly_units = data["hourly_units"]
    temperature_unit = hourly_units["temperature_2m"]

    precip_list = []

    for i in range(start_idx, start_idx+9):
        precip_list.append(hourly["precipitation"][i])

    maxP = 20 if temperature_unit == "°F" else 50
    minP = 0

    max_precip = max(precip_list) if precip_list else maxP
    min_precip = min(precip_list) if precip_list else minP

    precip_chart = Chart(df.display, title=title)
    container.add_chart(precip_chart)
    precip_chart.set_values(precip_list)
    precip_chart.min_val = min_precip
    precip_chart.max_val = max_precip
    precip_chart.scale_to_fit = True
    precip_chart.data_colour = df.translate_color(settings.get("CHART_DATA_COLOR_PRECIP","_Green"))
    precip_chart.grid_colour = df.translate_color(settings.get("CHART_GRID_COLOR","_LightGray"))
    precip_chart.background_colour = df.translate_color(settings.get("CHART_BACKGROUND_COLOR","_White"))
    precip_chart.show_x_axis = False #lower left corner of x & y axis overlay each other
    precip_chart.show_y_axis = True
    precip_chart.show_datapoints = True
    precip_chart.data_point_radius = 1
    precip_chart.show_lines = True
    precip_chart.show_bars = False
    precip_chart.x = 0
    precip_chart.y = 0
    precip_chart.width = int(df.WIDTH)
    precip_chart.height = int(df.HEIGHT // divider)
    precip_chart.border_width = 0
    precip_chart.title_scale =2
    precip_chart.update()
    container.update()

def format_precipitation_data(data, settings):
    """
    Format and display the precipitation data based on the provided weather data and settings.
    
    Args:
        data (dict): The weather data dictionary containing current and hourly weather information.
        settings (dict): A dictionary containing the configuration settings.
        container (Located_Container): The container to which the chart and table will be added.
        start_idx (int): The starting index for the forecast data.
        title (str): The title for the precipitation chart.
        divider (int): The divider for determining the chart height.
    """
    log_debug("[openmeteo] format_precipitation_data()")
    global forecast_anchors
    global header_pen, data_pen, alert_pen, background_pen, date_pen
    df.cls()
    # starting row of text
    start_idx, forecast_time = get_start_idx(data)

    hourly = data["hourly"]
 
    # Format and print the header rows for the forecast data.
    date_time_text = hourly["time"][start_idx] # e.g. "yyyy-mo-ddThh:mm"
    date_text = date_time_text.split("T")[0]   # "yyyy-mo-dd"

    chart_height_divider = 5
    chart_height = df.HEIGHT // chart_height_divider
    table_height = df.HEIGHT - chart_height

    chart_container = Located_Container(df.display, width=df.WIDTH, height=chart_height,x=0,y=0)
    format_precipitation_chart(data,settings,chart_container, start_idx, "Precipitation", chart_height_divider)

    table_container = Located_Container(df.display, width=df.WIDTH, height = table_height,x=0, y=chart_height)
    
    hdr = Card(df.display,title=f"Precipitation {forecast_time}",width=df.WIDTH, fixed_width=True)
    table_container.add_chart(hdr)
    hdr.title_colour = df.translate_color(settings.get("TITLE_COLOR","_RoyalBlue"))

#    w1, w2, w3, w4, w5, w6, w7 = 6, 5, 5, 5, 5, 4, 4
    w1, w2, w3, w4, w5, w6, w7 = 5, 6, 6, 6, 6, 4, 4
    hdrText_XX = f"{'Time':>{w1}}{'Tot':>{w2}}{'xxxx':>{w3}}{'xxxx':>{w4}}{'Snow':>{w5}}{'Rel':>{w6}}{'Prob.':>{w7}}"
    hdrText = hdrText_XX.replace('xxxx','    ')
    dashlen = len(hdrText)
    hdr = TextCard(df.display,title=hdrText, width=df.WIDTH,fixed_width=True)
    table_container.add_chart(hdr)
    header_color = df.translate_color(settings.get("TABLE_HEADER_COLOR","_SlateBlue"))
    hdr.title_colour = header_color

    p_label = data["current_units"]["precipitation"]
    hhmm = "XXXX"
    hdrText_XX = f"{hhmm:>{w1}}{p_label:>{w2}}{'Rain':>{w3}}{'Shwr':>{w4}}{'Fall':>{w5}}{'Hum':>{w6}}{'%':>{w7}}"
    hdrText = hdrText_XX.replace(hhmm,"    ")
    hdr = TextCard(df.display,title=hdrText, width=df.WIDTH,fixed_width=True)
    table_container.add_chart(hdr)
    hdr.title_colour = header_color

    hdr = TextCard(df.display, title="-"*dashlen,width=df.WIDTH, fixed_width=True)
    table_container.add_chart(hdr)
    hdr.title_colour= header_color

    # iterate through the next N hours of data starting from the current hour to determine the
    # highest temperature in the forecast period. We will use this to highlight the row with the highest temp.
    tempList = hourly["temperature_2m"]
    maxidx, maxtemp = max(enumerate(tempList[start_idx:start_idx+9]), key=lambda t: t[1])
    maxidx += start_idx
    log_debug(f"{maxidx}:{maxtemp}")
    # Now iterate through the data again to print it out, this time highlighting the row with the highest temperature.
    date_text_old = ""
    for i in range(start_idx, start_idx + 9):
        date_time_text = hourly["time"][i] # e.g. "yyyy-mo-ddThh:mm"
        date_text = date_time_text.split("T")[0] # "yyyy-mo-dd"
        if date_text != date_text_old:
            card = Card(df.display,title=date_text, width=df.WIDTH, fixed_width=True)
            table_container.add_chart(card)
            card.title_colour = df.translate_color(settings.get("TITLE_COLOR","_RoyalBlue"))
        date_text_old = date_text

        # Extract just the hour
        time_text = date_time_text.split("T")[1] # "hh:mm"

        precipitation = hourly["precipitation"][i]
        rain = hourly["rain"][i]
        showers = hourly["showers"][i]
        snowfall = hourly["snowfall"][i]
        apparent_temp = hourly["apparent_temperature"][i]
        precipitation_probability = hourly["precipitation_probability"][i]
        rel_humidity = hourly["relative_humidity_2m"][i]

        line = f"{time_text:>{w1}}{precipitation:>{w2}}{rain:>{w3}}{showers:>{w4}}{snowfall:>{w5}}{rel_humidity:>{w6}}{precipitation_probability:>{w7}}"
        card = TextCard(df.display,title=line,width=df.WIDTH,fixed_width=True)
        table_container.add_chart(card)
        card.title_colour = df.translate_color(settings.get("TABLE_DATA_COLOR","_PaleTurquoise"))

    log_debug(f"Available keys: {list(settings.keys())}")
    for idx, card in enumerate(table_container.charts):
        if idx == 0:
            print(f"Bkgrd clr: {settings.get('TABLE_BACKGROUND_COLOR')}")
        card.background_colour = df.translate_color(settings.get("TABLE_BACKGROUND_COLOR","_Black"))
        card.border_width = 0
        card._display.set_font("Roboto_Medium.af")
        card.update()
        log_debug(card.title)
    
    table_container.update()
    chart_container.update()
    df.refresh()
    log_debug("...end format_precipitation_data()")

def consolidate_weather_codes(code):
    """
    Consolidate the weather code into a broader category based on predefined groups.
    
    Args:
        code (int): The weather code that was returned by the openmeteo API to be consolidated.
    
    Returns:
        str: The consolidated weather category.
    """
    log_debug("[openmeteo] consolidate_weather_codes()")
    for c in WEATHER_GROUPS:
        if code in c:
            return WEATHER_GROUPS[c]
    return f"--- weather code {code} ---"

def format_forecast_chart(data, settings, container, start_idx,title, divider):
    """
    Format the forecast chart based on the provided weather data and settings.
    
    Args:
        data (dict): The weather data dictionary containing current and hourly weather information.
        settings (dict): A dictionary containing the configuration settings.
        container (Located_Container): The container to which the chart will be added.
        start_idx (int): The starting index for the forecast data.
        title (str): The title for the forecast chart.
        divider (int): The divider for determining the chart height.
    
    Returns:
        None
    """
    log_debug("[openmeteo] format_forecast_chart()")
    hourly = data["hourly"]
    hourly_units = data["hourly_units"]
    temperature_unit = hourly_units["temperature_2m"]

    temp_list = []   

    # build the four lists for the four charts. Each list will have 9 entries, 
    # starting with the current hour. So if it's 3:15pm now, the first entry will be for 3:00pm, then 4:00pm, etc.
    for i in range(start_idx, start_idx + 9):
        temp_list.append(hourly["temperature_2m"][i])
    
    minT = -20 if temperature_unit == "°F" else -28
    maxT = 120 if temperature_unit == "°F" else 50

    min_temp = min(temp_list) if temp_list else minT
    max_temp = max(temp_list) if temp_list else maxT


    log_debug(f"(format_forecast_chart) Max temp: {max_temp}  Min temp: {min_temp}")

    temperature_chart = Chart(df.display, title=title)
    container.add_chart(temperature_chart)
    temperature_chart.set_values(temp_list)  # Initial values
    temperature_chart.min_val = min_temp
    temperature_chart.max_val = max_temp
    temperature_chart.scale_to_fit = True
    temperature_chart.data_colour = df.translate_color(settings.get("CHART_DATA_COLOR_TEMP","_Red"))
    temperature_chart.grid_colour = df.translate_color(settings.get("CHART_GRID_COLOR","_LightGray"))
    temperature_chart.background_colour = df.translate_color(settings.get("CHART_BACKGROUND_COLOR","_White"))
    temperature_chart.show_x_axis = False #lower left corner of x & y axis overlay each other
    temperature_chart.show_y_axis = True
    temperature_chart.show_datapoints = True
    temperature_chart.data_point_radius = 1
    temperature_chart.show_lines = True
    temperature_chart.show_bars = False
    temperature_chart.x = 0
    temperature_chart.y = 0
    temperature_chart.width = int(df.WIDTH)
    temperature_chart.height = int(df.HEIGHT // divider)
    temperature_chart.border_width = 0
    temperature_chart.title_scale = 2
    temperature_chart.update()
    container.update()

def format_forecast_data(data, settings):
    """
    Format and display the forecast data based on the provided weather data and settings.
    
    Args:
        data (dict): The weather data dictionary containing current and hourly weather information.
        settings (dict): A dictionary containing the configuration settings.
        start_idx (int): The starting index for the forecast data.
        title (str): The title for the forecast chart.
        divider (int): The divider for determining the chart height.
        
        Returns:
            None
    """
    log_debug("[openmeteo] format_forecast_data()")
    global forecast_anchors
    df.cls()
    start_idx, forecast_time = get_start_idx(data)
    
    temperature_label = data["hourly_units"]["temperature_2m"]
    wind_speed_label = data["hourly_units"]["wind_speed_10m"]
    #uv_label = data["hourly_units"]["uv_index"]

    # iterate through the next N hours of data starting from the current hour, or as close to it as we can get with the data we have.
            # 1. Define where each column SHOULD end (Right Anchor)

    hourly = data["hourly"]

    # Format and print the header rows for the forecast data.
    date_time_text = hourly["time"][start_idx] # e.g. "yyyy-mo-ddThh:mm"
    date_text = date_time_text.split("T")[0]   # "yyyy-mo-dd"

    chart_height_divider = 5 # chart is 1 / chart_height_divider of screen
    chart_height = df.HEIGHT // chart_height_divider
    table_height = df.HEIGHT - chart_height
    chart_container = Located_Container(df.display,width=df.WIDTH,height=chart_height,x=0,y=0)
    format_forecast_chart(data, settings, chart_container, start_idx, f"Temp {temperature_label}", chart_height_divider)

    table_container = Located_Container(df.display,width=df.WIDTH,height=table_height,x=0,y=chart_height)

    hdr = Card(df.display,title=f"Weather forecast as of {forecast_time}",width=df.WIDTH,fixed_width = True)
    table_container.add_chart(hdr)
    hdr.title_colour = df.translate_color(settings.get("TITLE_COLOR","_RoyalBlue"))

    header_color = df.translate_color(settings.get("TABLE_HEADER_COLOR","_SlateBlue"))
    
    w1, w2, w3, w4, w5, w6 = 6, 6, 6, 5, 6, 7
    GAP = "  "
    hdrText = f"{'Time':>{w1}}{'Temp':>{w2}}{'Feels':>{w3}}{'Wind':>{w4}}{'UV':>{w5}}{GAP}{'Desc':<{w6}}"
    dashlen = len(hdrText)
    hdr = TextCard(df.display,title=hdrText,width=df.WIDTH,fixed_width=True)
    table_container.add_chart(hdr)
    hdr.title_colour = header_color

    hhmm = 'hh:mm'
    hdrText_XX = f"{hhmm:>{w1}}{'XX':>{w2}}{'Like':>{w3}}{wind_speed_label.strip():>{w4}}{'Index':>{w5}}"
    hdrText = hdrText_XX.replace('XX',temperature_label.strip())
    #hdrText = f"{hhmm:>{w1}}{temperature_label.strip():>{w2}}{'Like':>{w3}}{wind_speed_label.strip():>{w4}}{'Index':>{w5}}"
    hdr = TextCard(df.display,title=hdrText,width=df.WIDTH,fixed_width=True)
    table_container.add_chart(hdr)
    hdr.title_colour = header_color

    hdr = TextCard(df.display,title="-"*dashlen,width=df.WIDTH,fixed_width=True)
    table_container.add_chart(hdr)
    hdr.title_colour = header_color

    # iterate through the next N hours of data starting from the current hour to determine the
    # highest temperature in the forecast period. We will use this to highlight the row with the highest temp.
    maxidx, maxtemp = max(enumerate(hourly["temperature_2m"][start_idx:start_idx+9]), key=lambda t: t[1])
    maxidx += start_idx
    
    # Now iterate through the data again to print it out, this time highlighting the row with the highest temperature.
    date_text_old = ""
    for i in range(start_idx, start_idx + 9):
        date_time_text = hourly["time"][i] # e.g. "yyyy-mo-ddThh:mm"
        date_text = date_time_text.split("T")[0] # "yyyy-mo-dd"
        if date_text != date_text_old:
            card = Card(df.display,title=date_text,width=df.WIDTH,fixed_width = True)
            table_container.add_chart(card)
            card.title_colour = df.translate_color(settings.get("TITLE_COLOR","_RoyalBlue"))
        date_text_old = date_text

        # Extract just the hour
        time_text = date_time_text.split("T")[1] # "hh:mm"

        temp = hourly["temperature_2m"][i]
        apparent_temp = hourly["apparent_temperature"][i]
        #temp = f"{temp:02.1f}({apparent_temp:02.1f})"
        weather_code = hourly["weather_code"][i]

        wind_speed = hourly["wind_speed_10m"][i]
        uv = hourly["uv_index"][i]

        if uv == None:
            uv = "n/a"
        else:
            uv = f"{uv:2.1f}"

        line = f"{time_text:>{w1}}{temp:>{w2}}{apparent_temp:>{w3}}{wind_speed:>{w4}}{uv:>{w5}}{GAP}{consolidate_weather_codes(weather_code):<{w6}}"
        card = TextCard(df.display,title=line,width=df.WIDTH,fixed_width = True)
        table_container.add_chart(card)
        #highlight the highest temp in the request
        if i == maxidx:
            card.title_colour = df.translate_color(settings.get("TABLE_ALERT_COLOR","_Coral"))
        else:
            card.title_colour = df.translate_color(settings.get("TABLE_DATA_COLOR","_PaleTurquoise"))

        log_debug(f"{time_text} | {temp}{temperature_label} | {wind_speed}{wind_speed_label} | uv index: {uv} | {consolidate_weather_codes(weather_code)}")

    # After drawing all the lines, refresh the display to show the new data
    for idx, card in enumerate(table_container.charts):
        card.background_colour = df.translate_color(settings.get("TABLE_BACKGROUND_COLOR","_Black"))
        #log_debug(f"Background Color: {card.background_colour}")
        card.border_width = 0
        card._display.set_font("Roboto_Medium.af") #bitmap8")
        card.update()
        log_debug(card.title)
    
    table_container.update()
    chart_container.update()
    df.refresh()
    log_debug("...end format_forecast_data()")

def format_N_day_forecast_data(data, settings):
    """
    Format and display the N-day forecast data based on the provided weather data and settings.
    
    Args:
        data (dict): The weather data dictionary containing current and daily weather information.
        settings (dict): A dictionary containing the configuration settings.
        
    Returns:
        None
    """
    global forecast_anchors
    log_debug("[openmeteo] format_N_day_forecast_data()")
    df.cls()
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
    N = settings.get("N_DAY_FORECAST", 5)
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

    daily_max = -999
    max_temp_daily_idx = -1
    for i in range(0, len(daily["time"])):
        max_temp = daily["temperature_2m_max"][i]
        if max_temp > daily_max:
            daily_max = max_temp
            max_temp_daily_idx = i

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
        if i == max_temp_daily_idx:
            pen = alert_pen
        else:
            pen = data_pen
            
        if anchored:
            line = [h1,h2,h3,h4]
            df.draw_vector_row(line,row_y,pen,anchors=N_day_forecast_anchors)
        else:
            line = [f"{h1:12s}{h2:<12s}{h3:<7s}{h4:>6s}"]
            df.draw_vector_row(line, row_y, pen, anchors=[])

        row_y += df.row_step
        log_debug(line)

    try:
        df.refresh()
    except Exception as e:
        log_debug(f"Error refreshing display: {e}")

    log_debug("...end format_N_day_forecast_data()")

async def get_forecast_data(settings):
    """
    Fetch the weather forecast data from the Open-Meteo API based on the provided settings.
    
    Args:
        settings (dict): A dictionary containing the configuration settings.
    Returns:
        data (dict): The weather forecast data.
    """
    log_debug("[openmeteo] get_forecast_data()")
    gc.collect()
    
    host = "api.open-meteo.com"
    LATITUDE = settings.get("LATITUDE", 54)
    LONGITUDE = settings.get("LONGITUDE", 0)
    UNITS = settings.get("UNITS", "imperial")
    n_day_forecast = settings.get("N_DAY_FORECAST", 5)
    log_debug(UNITS)
    if UNITS == "imperial":
        temperature_unit = "fahrenheit"
        wind_speed_unit = "mph"
        precipitation_unit = "inch"
    else:
        temperature_unit = "celsius"
        wind_speed_unit = "kmh"
        precipitation_unit = "mm"
    
    # 1. ORGANIZE PARAMS CLEANLY
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": "temperature_2m,apparent_temperature,precipitation_probability,precipitation,rain,showers,snowfall,weather_code,cloud_cover,wind_speed_10m,relative_humidity_2m,uv_index",
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,showers,snowfall,weather_code,cloud_cover,wind_speed_10m,uv_index",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
        "timezone": "auto",
        "forecast_days": int(n_day_forecast),
        "models": "best_match",
        "wind_speed_unit": wind_speed_unit,
        "temperature_unit": temperature_unit,
        "precipitation_unit": precipitation_unit
    }
    
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    path = f"/v1/forecast?{query_string}"
    
    # 2. THE RAW HTTP REQUEST CONSTRUCTION
    # Note: Using distinct lines with explicit \r\n to guarantee protocol compliance.
    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"User-Agent: Presto_WeatherStation_RP2350\r\n"
        f"Connection: close\r\n\r\n"
    )
    
    log_debug("="*60)
    log_debug("      DIAGNOSTIC OUTBOUND SOCKET PACKET")
    log_debug("="*60)
    log_debug(request)  # This lets you see exactly what the socket sees
    log_debug("="*60 + "\n")
    
    try:
        log_debug(f"[Socket] Resolving and opening SSL pipe to {host}:443...")
        reader, writer = await asyncio.open_connection(host, 443, ssl=True)
        log_debug("[Socket] Connection established successfully!")
        
        # Burst data onto the wire
        writer.write(request.encode('utf-8'))
        await writer.drain()
        log_debug("[Socket] Request data successfully flushed down the pipe.")
        
        # 3. INTERCEPT AND LOG RAW RECOVERY TRAFFIC
        log_debug("\n[Socket] Reading response headers...")
        
        # Read the first line of the server response to check the HTTP Status Code
        status_line = await reader.readline()
        log_debug(f" -> SERVER STATUS CODE: {status_line.decode('utf-8').strip()}")
        
        content_length = 0
        is_chunked = False
        
        # Consume the rest of the headers
        while True:
            line = await reader.readline()
            if line == b'\r\n' or line == b'\n' or not line:
                break
            header_str = line.decode('utf-8').lower()
            if "content-length:" in header_str:
                content_length = int(header_str.split("content-length:")[1].strip())
            elif "transfer-encoding:" in header_str and "chunked" in header_str:
                is_chunked = True

        # Read the raw body bytes completely
        body_bytes = bytearray()
        if is_chunked:
            while True:
                size_line = await reader.readline()
                if not size_line: break
                size_str = size_line.decode('utf-8').strip().split(';')[0]
                if not size_str: continue
                chunk_size = int(size_str, 16)
                if chunk_size == 0:
                    await reader.readline()
                    break
                bytes_read = 0
                while bytes_read < chunk_size:
                    chunk = await reader.read(chunk_size - bytes_read)
                    if not chunk: break
                    body_bytes.extend(chunk)
                    bytes_read += len(chunk)
                await reader.readline()
        elif content_length > 0:
            while len(body_bytes) < content_length:
                chunk = await reader.read(min(content_length - len(body_bytes), 512))
                if not chunk: break
                body_bytes.extend(chunk)
        else:
            while True:
                chunk = await reader.read(512)
                if not chunk: break
                body_bytes.extend(chunk)

        # Convert to text string
        body_text = body_bytes.decode('utf-8').strip()
        
        log_debug("="*60)
        log_debug("      DIAGNOSTIC INBOUND RAW RESPONSE FROM SERVER")
        log_debug("="*60)
        # Peek at the response. If the query failed, Open-Meteo tells why here
        log_debug(body_text[:1000]) 
        log_debug("="*60 + "\n")
        
        # 4. STRUCTURAL JSON VALIDATION CHECK
        if not body_text.startswith("{"):
            log_debug("[Diagnostic Error] Stop! The server returned plain text or an error page, not JSON.")
            return None
            
        data = json.loads(body_text)
        return data

    except Exception as e:
        log_debug(f"[Diagnostic Fatal Crash] Socket error occurred: {e}")
        return None
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
        gc.collect()

def format_current_parameters(settings, defaults, city, IP_ADDRESS, utc_offset_seconds):
    """
    show the options currently in effect (longitude, latitude, days of forecast, ...)

    args:
        settings (dict): The current settings dictionary.
        defaults (dict): The default settings dictionary.
        city (str): The city name returned by OpenStreetMap.
        now_list (list): A list containing the current hour and minute.
        IP_ADDRESS (str): The IP address of the device.
    
    Returns:
        None
    """
    log_debug("[openmeteo] format_current_parameters()")
    longitude = settings.get("LONGITUDE",defaults["LONGITUDE"])
    latitude = settings.get("LATITUDE",defaults["LATITUDE"])
    debug = settings.get("DEBUG",defaults["DEBUG"])
    query_interval = settings.get("QUERY_INTERVAL_MINUTES",defaults["QUERY_INTERVAL_MINUTES"])
    start_hour = settings.get("START_HOUR",defaults["START_HOUR"])
    end_hour = settings.get("END_HOUR",defaults["END_HOUR"])
    local_longitude = settings.get("LOCAL_LONGITUDE",defaults["LOCAL_LONGITUDE"])
    local_latitude = settings.get("LOCAL_LATITUDE",defaults["LOCAL_LATITUDE"])
    units = settings.get("UNITS",defaults["UNITS"])
    days_of_forecast = settings.get("N_DAY_FORECAST",defaults["N_DAY_FORECAST"])
    parms = [["Longitude:",str(longitude)], # modifiable on web interface
             ["Latitude:", str(latitude)],  # modifiable on web interface 
             ["Location:", city], # returned by open street map
             ["Query Interval:",str(query_interval)], # modifiable on web interface
             ["Units:",units], # modifiable on web interface
             ["Forecast Days:",str(days_of_forecast)], # modifiable on web interface
             [" "," "],
             ["Local longitude:",str(local_longitude)], #not modifiable on web interface
             ["Local latitude:", str(local_latitude)],  #not modifiable on web interface
             ["Starting hour:",str(start_hour)], # modifiable on web interface
             ["Ending hour:",str(end_hour)] # modifiable on web interface
    ]
    df.cls()
    anchored = True
    anchors = [120,  200]

    global header_pen, data_pen, alert_pen, background_pen, date_pen
    
    # starting row of text
    row_y = 20

    # Format and print the header rows for the forecast data.
    now = time.gmtime(time.time() + utc_offset_seconds)
    line = [f"Current Operating Parameters @{now[3]:02}:{now[4]:02}"]
    df.draw_vector_row(line, row_y, date_pen, anchors=[])
    row_y += df.row_step
    line = [f"Config IP Address:", f"{IP_ADDRESS}"]
    df.draw_vector_row(line, row_y, data_pen, anchors=anchors)
    row_y += df.row_step

    for parm in parms:
        df.draw_vector_row(parm,row_y,data_pen,anchors=anchors)
        row_y += df.row_step

    desc = ["-> local long. & lat., start & end hours"]
    df.draw_vector_row(desc,row_y, alert_pen,anchors=[])
    row_y += df.row_step
    desc = ["   control polling dormancy time."]
    df.draw_vector_row(desc, row_y, alert_pen, anchors=[])
    #row_y += df.row_step

    try:
        df.refresh()
    except Exception as e:
        log_debug(f"Error refreshing display: {e}")

    log_debug("[openmeteo]...end format_current_parameters(")

def temp_wind_uv_charts(data):
    """
    Format and display temperature, wind speed, and UV index charts based on the provided weather data.
    
    Args:
        data (dict): The weather data dictionary containing current and hourly weather information.
    
    Returns:
        None
    """
    log_debug("[open_meteo] temp_wind_uv_charts()")
    current = data["current"]
    hourly = data["hourly"]

    hourly_units = data["hourly_units"]
    temperature_unit = hourly_units["temperature_2m"]
    apparent_temperature_unit = hourly_units["apparent_temperature"]
    wind_speed_unit = hourly_units["wind_speed_10m"]
    uv_index_unit = hourly_units["uv_index"]

    current_date_time = current["time"]
    current_hour_api = current_date_time[:13] + ":00"

    temp_list = []   
    apparent_list = []
    wind_list = []
    uv_list = []

    # Find where this hour exists in the hourly list
    try:
        start_idx = hourly["time"].index(current_hour_api)
    except ValueError:
        # Fallback to 0 if for some reason the current hour isn't in the data
        start_idx = 0

    # build the four lists for the four charts. Each list will have 9 entries, 
    # starting with the current hour. So if it's 3:15pm now, the first entry will be for 3:00pm, then 4:00pm, etc.
    for i in range(start_idx, start_idx + 9):
        temp_list.append(hourly["temperature_2m"][i])
        apparent_list.append(hourly["apparent_temperature"][i])
        wind_list.append(hourly["wind_speed_10m"][i])
        uv_list.append(hourly["uv_index"][i])

    minT = -20 if temperature_unit == "°F" else -5
    maxT = 120 if temperature_unit == "°F" else 40

    min_temp = min(temp_list) if temp_list else minT
    max_temp = max(temp_list) if temp_list else maxT

    min_apparent = min(apparent_list) if apparent_list else min
    max_apparent = max(apparent_list) if apparent_list else maxT

    minW = 0
    maxW = 120 if wind_speed_unit == "mp/h" or wind_speed_unit == "mph" else 180
    min_wind = min(wind_list) if wind_list else minW
    max_wind = max(wind_list) if wind_list else maxW

    min_uv = min(uv_list) if uv_list else 0
    max_uv = max(uv_list) if uv_list else 10

    log_debug(f"Max temp: {max_temp}  Min temp: {min_temp}")
    log_debug(f"Max apparent temp: {max_apparent}  Min apparent temp: {min_apparent}")
    log_debug(f"Max wind: {max_wind}  Min wind: {min_wind}")
    log_debug(f"Max uv: {max_uv}  Min uv: {min_uv}")

    container = Container(display)
    temperature_chart = Chart(display, title=f"Temp {temperature_unit}")
    apparent_chart = Chart(display, title = f"Feels like {apparent_temperature_unit}")
    wind_chart = Chart(display, title = f"Wind Speed {wind_speed_unit}")
    uv_chart = Chart(display, title = f"UV Index {uv_index_unit}")

    container.add_chart(temperature_chart)
    container.add_chart(apparent_chart)
    container.add_chart(wind_chart)
    container.add_chart(uv_chart)
    container.cols = 2
    container.update()

    temperature_chart.set_values(temp_list)  # Initial values
    temperature_chart.min_val = min_temp
    temperature_chart.max_val = max_temp
    temperature_chart.scale_to_fit = True
    temperature_chart.data_colour = chart_data_color_temp
    temperature_chart.grid_colour = chart_grid_color
    temperature_chart.background_colour = chart_background_color
    temperature_chart.show_x_axis = False
    temperature_chart.show_y_axis = True
    temperature_chart.show_datapoints = True
    temperature_chart.data_point_radius = 1
    temperature_chart.show_lines = True
    temperature_chart.show_bars = False
    temperature_chart.x = 0
    temperature_chart.y = 0
    temperature_chart.width = int(WIDTH / 2)
    temperature_chart.height = int(HEIGHT / 2)
    temperature_chart.border_width = 0
    temperature_chart.update()
  
    apparent_chart.set_values(apparent_list)  # Initial values
    apparent_chart.min_val = min_apparent
    apparent_chart.max_val = max_apparent
    apparent_chart.scale_to_fit = True
    apparent_chart.data_colour = chart_data_color_temp
    apparent_chart.grid_colour = chart_grid_color
    apparent_chart.background_colour = chart_background_color
    apparent_chart.show_y_axis = True
    apparent_chart.show_datapoints = True
    apparent_chart.data_point_radius = 1
    apparent_chart.show_lines = True
    apparent_chart.show_bars = False
    apparent_chart.x = int(WIDTH / 2)
    apparent_chart.y = 0
    apparent_chart.width = int(WIDTH / 2)
    apparent_chart.height = int(HEIGHT / 2)
    apparent_chart.border_width = 1
    apparent_chart.update()

    wind_chart.set_values(wind_list)  # Initial values
    wind_chart.min_val = min_wind
    wind_chart.max_val = max_wind
    wind_chart.scale_to_fit = True
    wind_chart.data_colour = chart_data_color_temp
    wind_chart.grid_colour = chart_grid_color
    wind_chart.background_colour = chart_background_color
    wind_chart.show_y_axis = True
    wind_chart.show_datapoints = True
    wind_chart.data_point_radius = 1
    wind_chart.show_lines = True
    wind_chart.show_bars = False
    wind_chart.x = 0
    wind_chart.y = int(HEIGHT / 2)
    wind_chart.width = int(WIDTH / 2)
    wind_chart.height = int(HEIGHT / 2)
    wind_chart.border_width = 1
    wind_chart.update()
  
    uv_chart.set_values(uv_list)  # Initial values
    uv_chart.min_val = (int(min_uv) // 10) * 10.0  # Typical min temperature in °C
    uv_chart.max_val = (int(max_uv) // 10) * 10.0  # Typical max temperature in °C
    uv_chart.scale_to_fit = True
    uv_chart.data_colour = chart_data_color_temp
    uv_chart.grid_colour = chart_grid_color
    uv_chart.background_colour = chart_background_color
    uv_chart.show_y_axis = True
    uv_chart.show_datapoints = True
    uv_chart.data_point_radius = 1
    uv_chart.show_lines = True
    uv_chart.show_bars = False
    uv_chart.x = int(WIDTH / 2)
    uv_chart.y = int(HEIGHT / 2)
    uv_chart.width = int(WIDTH / 2)     
    uv_chart.height = int(HEIGHT / 2)
    uv_chart.border_width = 1
    uv_chart.update()

    presto.update()

def precipitation_charts(data):
    """
    Format and display precipitation charts based on the provided weather data.
    
    Args:
        data (dict): The weather data dictionary containing current and hourly weather information.

    Returns:
        None
    """
    log_debug("[open_meteo] precipitation_charts()")
    current = data["current"]
    hourly = data["hourly"]

    current_date_time = current["time"]
    current_hour_api = current_date_time[:13] + ":00"

    precipitation_list = []
    rain_list = []   
    showers_list = []
    snowfall_list = []
    
    # Find where this hour exists in the hourly list
    try:
        start_idx = hourly["time"].index(current_hour_api)
    except ValueError:
        # Fallback to 0 if for some reason the current hour isn't in the data
        start_idx = 0

    for i in range(start_idx, start_idx + 9):
        precipitation_list.append(hourly["precipitation"][i])
        rain_list.append(hourly["rain"][i])
        showers_list.append(hourly["showers"][i])
        snowfall_list.append(hourly["snowfall"][i])

    min_precipitation = min(precipitation_list) if precipitation_list else 0
    max_precipitation = max(precipitation_list) if precipitation_list else 10
    
    log_debug(f"Max precipitation: {max_precipitation}  Min precipitation: {min_precipitation}")
    
    precipitation_chart = Chart(display, title="precipitation")
    precipitation_chart.set_values(precipitation_list)  # Initial values
    precipitation_chart.min_val = min_precipitation
    precipitation_chart.max_val = max_precipitation
    precipitation_chart.scale_to_fit = True
    precipitation_chart.data_colour = chart_data_color_precip
    precipitation_chart.grid_colour = chart_grid_color
    precipitation_chart.background_colour = chart_background_color
    precipitation_chart.show_y_axis = True
    precipitation_chart.show_datapoints = True
    precipitation_chart.data_point_radius = 1
    precipitation_chart.show_lines = True
    precipitation_chart.show_bars = False
    precipitation_chart.x = 0
    precipitation_chart.y = 0
    precipitation_chart.width = WIDTH
    precipitation_chart.height = int(HEIGHT / 4)
    precipitation_chart.title_scale = 2
    precipitation_chart.update()

    min_rain = min(rain_list) if rain_list else 0
    max_rain = max(rain_list) if rain_list else 10
    
    log_debug(f"Max rain: {max_rain}  Min rain: {min_rain}")

    rain_chart = Chart(display, title = "rain")
    rain_chart.set_values(rain_list)  # Initial values
    rain_chart.min_val = min_rain
    rain_chart.max_val = max_rain
    rain_chart.scale_to_fit = True
    rain_chart.data_colour = chart_data_color_precip
    rain_chart.grid_colour = chart_grid_color
    rain_chart.background_colour = chart_background_color
    rain_chart.show_y_axis = True
    rain_chart.show_datapoints = True
    rain_chart.data_point_radius = 1
    rain_chart.show_lines = True
    rain_chart.show_bars = False
    rain_chart.x = 0
    rain_chart.y = int(HEIGHT / 4)
    rain_chart.width = WIDTH
    rain_chart.height = int(HEIGHT / 4)
    rain_chart.title_scale = 2
    rain_chart.update()

    min_showers = min(showers_list) if showers_list else 0
    max_showers = max(showers_list) if showers_list else 10
    log_debug(f"Max showers: {max_showers}  Min showers: {min_showers}")

    showers_chart = Chart(display, title = "showers")
    showers_chart.set_values(showers_list)  # Initial values
    showers_chart.min_val = min_showers
    showers_chart.max_val = max_showers
    showers_chart.scale_to_fit = True
    showers_chart.data_colour = chart_data_color_precip
    showers_chart.grid_colour = chart_grid_color
    showers_chart.background_colour = chart_background_color
    showers_chart.show_y_axis = True
    showers_chart.show_datapoints = True
    showers_chart.data_point_radius = 1
    showers_chart.show_lines = True
    showers_chart.show_bars = False
    showers_chart.x = 0
    showers_chart.y = int(HEIGHT / 2)
    showers_chart.width = WIDTH
    showers_chart.height = int(HEIGHT / 4)
    showers_chart.title_scale = 2
    showers_chart.update()

    min_snowfall = min(snowfall_list) if snowfall_list else 0
    max_snowfall = max(snowfall_list) if snowfall_list else 10
    log_debug(f"Max snowfall: {max_snowfall}  Min snowfall: {min_snowfall}")

    snowfall_chart = Chart(display, title = "snowfall")
    snowfall_chart.set_values(snowfall_list)  # Initial values
    snowfall_chart.min_val = min_snowfall
    snowfall_chart.max_val = max_snowfall
    snowfall_chart.scale_to_fit = True
    snowfall_chart.data_colour = chart_data_color_precip
    snowfall_chart.grid_colour = chart_grid_color
    snowfall_chart.background_colour = chart_background_color
    snowfall_chart.show_y_axis = True
    snowfall_chart.show_datapoints = True
    snowfall_chart.data_point_radius = 1
    snowfall_chart.show_lines = True
    snowfall_chart.show_bars = False
    snowfall_chart.x = 0
    snowfall_chart.y = int(HEIGHT - HEIGHT / 4)
    snowfall_chart.width = WIDTH
    snowfall_chart.height = int(HEIGHT / 4)
    snowfall_chart.title_scale = 2
    snowfall_chart.update()

    presto.update()

