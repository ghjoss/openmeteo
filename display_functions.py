from control import TESTING
import control
import picovector
from presto import Presto
import Colors as colors

def init_provider(presto_obj, rotational_shift=None, scale = None, font = None):
    global BLACK, WHITE, WIDTH, HEIGHT
    global display, presto, vector
    global default_font, default_scale, default_rotational_shift
    global row_step, small_step

    presto = presto_obj
    display = presto.display
    vector = picovector.PicoVector(display)
    vector.set_antialiasing(picovector.ANTIALIAS_BEST)

    default_scale = 15
    row_step = 15
    small_step = 7
    default_font = "Roboto-Medium.af" # No degree symbol
    #default_font = "Roboto-Medium-With-Material-Symbols.af" #lowercase "t" is bad
    default_rotational_shift = -15
   
    if scale is None:
        pass
    else:
        print(f"Setting display scale to {scale}. Was {default_scale}.")
        default_scale = scale

    if font is None:
        pass
    else:
        print(f"Setting display font to {font}. Was {default_font}.")
        default_font = font
    
    vector.set_font(default_font, default_scale)
 
    if rotational_shift is None:
        pass
    else:
        print(f"Setting display rotational shift to {rotational_shift}. Was {default_rotational_shift}.")
        default_rotational_shift = rotational_shift

    BLACK = display.create_pen(0,0,0)
    WHITE = display.create_pen(255,255,255)
    WIDTH,HEIGHT = display.get_bounds()
    print(f"Display initialized with width={WIDTH}, height={HEIGHT}, scale={default_scale}, font={default_font}, row_step={row_step}, small_step={small_step}")      

def set_rotational_shift(rotational_shift,y_pos):
    t = picovector.Transform()
    t.rotate(default_rotational_shift,(0,y_pos)) # The corrective "leveling" tilt
    vector.set_transform(t)

def cls(bg=None):
    """
    clear the display

    Args:
        bg: background color to use

    Returns:
        no return value
    """
    global BLACK
    if bg is None:
        bg = BLACK
    display.set_pen(bg)
    display.clear()
    presto.update()

def set_backlight(brightness,level=0.1):
    lcl_brightness = brightness + level
    if lcl_brightness < 0:
        lcl_brightness = 0
    elif lcl_brightness > 1:
        lcl_brightness = 1
    presto.set_backlight(lcl_brightness)
    presto.update()
    return lcl_brightness


def presto_errors(msg):
    """
        Display an error message on the Presto display.
        Note: This function creates a new Presto instance to ensure that it can display the error message even if 
              the main Presto instance is not functioning properly.
              It clears the display and shows the provided error message in white text on a black background.
        Args:
            msg: the error message to be displayed
        Returns:
            no return value
    """
    lcl_presto = Presto()
    lcl_display = lcl_presto.display
    black_pen = lcl_display.create_pen(0,0,0)
    lcl_display.set_pen(black_pen)
    lcl_display.clear()
    white_pen = lcl_display.create_pen(255,255,255)
    lcl_display.set_pen(white_pen)
    lcl_display.text(msg, 5, 10, 240, 0.75)
    lcl_presto.update()

def draw_vector_row(texts, y_pos,pen,anchors=[]):

    """
    Draw a row of text on the display using picovector, with optional right-alignment based on anchors.
    Args:        texts: list of text strings to draw in the row
        y_pos: the y position for the row
        pen: the pen color to use for drawing the text
        anchors: optional list of x positions for right-aligning each text string. If empty, text will be left-aligned starting at x=5.
    Returns:        no return value
    """

    global display, vector, default_scale
    set_rotational_shift(default_rotational_shift,y_pos)

    # Set to your Red color
    display.set_pen(pen)
    
    # Use Integer Scale 1
    measureScale = 1
    for i in range(len(texts)):
        # Measure width to calculate right-alignment
        w = int(vector.measure_text(texts[i], measureScale)[2])
        
        # Draw: Force X and Y to integers
        if len(anchors) > 0:
            x_pos = int(anchors[i] - w)
        else:
            x_pos = 5
        t = picovector.Transform()
        t.rotate(default_rotational_shift,0)#(x_pos,y_pos)) # The corrective "leveling" tilt
        #t.scale(1.0,1.0)
        vector.set_transform(t)
        vector.text(texts[i], x_pos, int(y_pos), default_scale)

def refresh():
    presto.update()

def get_color(key):
    return colors.Colors[key]

def new_pen(color_name):
    pen_color = get_color(color_name)
    return display.create_pen(*pen_color)

def set_pen(pen):
    display.set_pen(pen)

