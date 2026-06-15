from pichart import Chart, Container,Card
import Colors
from control import FORECAST_HOURS, DEBUG, log_debug

def translate_color(color_name):
    color_dict = Colors.Colors[color_name]
    return {"red":color_dict[0],"green":color_dict[1],"blue":color_dict[2] }

def init_provider(main_presto):
    global presto, display, WIDTH,HEIGHT,forecast_hours

    log_debug("pichart_client_initialization")
    forecast_hours = FORECAST_HOURS
    presto = main_presto
    display = presto.display
    WIDTH, HEIGHT = display.get_bounds()
    
    global ALICE_BLUE,ORANGE,LIGHT_BLUE,GREEN,GRAY,WHITE,BLACK,PALE_TURQUOISE,RED
    ALICE_BLUE = translate_color("_AliceBlue")
    ORANGE = translate_color("_Orange")
    LIGHT_BLUE = translate_color("_LightBlue")
    GREEN = translate_color("_Green")
    GRAY = translate_color("_LightGray")
    WHITE = translate_color("_White")
    BLACK = translate_color("_Black")
    PALE_TURQUOISE = translate_color("_PaleTurquoise")
    RED = translate_color("_Red")
    
def temp_wind_uv_charts(data):
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

    # build the four lists for the four charts. Each list will have forecast_hours number of entries, 
    # starting with the current hour. So if it's 3:15pm now, the first entry will be for 3:00pm, then 4:00pm, etc.
    for i in range(start_idx, start_idx + forecast_hours):
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
    temperature_chart.data_colour = RED
    temperature_chart.grid_colour = GRAY
    temperature_chart.background_colour = WHITE
    temperature_chart.show_x_axis = True
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
    apparent_chart.data_colour = PALE_TURQUOISE
    apparent_chart.grid_colour = GRAY
    apparent_chart.background_colour = WHITE
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
    wind_chart.data_colour = PALE_TURQUOISE
    wind_chart.grid_colour = GRAY
    wind_chart.background_colour = WHITE
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
    uv_chart.data_colour = PALE_TURQUOISE
    uv_chart.grid_colour = GRAY
    uv_chart.background_colour = WHITE
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

    for i in range(start_idx, start_idx + forecast_hours):
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
    precipitation_chart.data_colour = GREEN
    precipitation_chart.grid_colour = GRAY
    precipitation_chart.background_colour = WHITE
    precipitation_chart.show_y_axis = True
    precipitation_chart.show_datapoints = True
    precipitation_chart.data_point_radius = 1
    precipitation_chart.show_lines = True
    precipitation_chart.show_bars = False
    precipitation_chart.x = 0
    precipitation_chart.y = 0
    precipitation_chart.width = WIDTH
    precipitation_chart.height = int(HEIGHT / 4)
    precipitation_chart.update()

    min_rain = min(rain_list) if rain_list else 0
    max_rain = max(rain_list) if rain_list else 10
    
    log_debug(f"Max rain: {max_rain}  Min rain: {min_rain}")

    rain_chart = Chart(display, title = "rain")
    rain_chart.set_values(rain_list)  # Initial values
    rain_chart.min_val = min_rain
    rain_chart.max_val = max_rain
    rain_chart.scale_to_fit = True
    rain_chart.data_colour = GREEN
    rain_chart.grid_colour = GRAY
    rain_chart.background_colour = WHITE
    rain_chart.show_y_axis = True
    rain_chart.show_datapoints = True
    rain_chart.data_point_radius = 1
    rain_chart.show_lines = True
    rain_chart.show_bars = False
    rain_chart.x = 0
    rain_chart.y = int(HEIGHT / 4)
    rain_chart.width = WIDTH
    rain_chart.height = int(HEIGHT / 4)
    rain_chart.update()

    min_showers = min(showers_list) if showers_list else 0
    max_showers = max(showers_list) if showers_list else 10
    log_debug(f"Max showers: {max_showers}  Min showers: {min_showers}")

    showers_chart = Chart(display, title = "showers")
    showers_chart.set_values(showers_list)  # Initial values
    showers_chart.min_val = min_showers
    showers_chart.max_val = max_showers
    showers_chart.scale_to_fit = True
    showers_chart.data_colour = GREEN
    showers_chart.grid_colour = GRAY
    showers_chart.background_colour = WHITE
    showers_chart.show_y_axis = True
    showers_chart.show_datapoints = True
    showers_chart.data_point_radius = 1
    showers_chart.show_lines = True
    showers_chart.show_bars = False
    showers_chart.x = 0
    showers_chart.y = int(HEIGHT / 2)
    showers_chart.width = WIDTH
    showers_chart.height = int(HEIGHT / 4)
    showers_chart.update()

    min_snowfall = min(snowfall_list) if snowfall_list else 0
    max_snowfall = max(snowfall_list) if snowfall_list else 10
    log_debug(f"Max snowfall: {max_snowfall}  Min snowfall: {min_snowfall}")

    snowfall_chart = Chart(display, title = "snowfall")
    snowfall_chart.set_values(snowfall_list)  # Initial values
    snowfall_chart.min_val = min_snowfall
    snowfall_chart.max_val = max_snowfall
    snowfall_chart.scale_to_fit = True
    snowfall_chart.data_colour = GREEN
    snowfall_chart.grid_colour = GRAY
    snowfall_chart.background_colour = WHITE
    snowfall_chart.show_y_axis = True
    snowfall_chart.show_datapoints = True
    snowfall_chart.data_point_radius = 1
    snowfall_chart.show_lines = True
    snowfall_chart.show_bars = False
    snowfall_chart.x = 0
    snowfall_chart.y = int(HEIGHT - HEIGHT / 4)
    snowfall_chart.width = WIDTH
    snowfall_chart.height = int(HEIGHT / 4)
    snowfall_chart.update()

    presto.update()

