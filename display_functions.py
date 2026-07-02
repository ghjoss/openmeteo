from control import log_debug
import picovector
from presto import Presto
#https://rgbcolorcode.com/
Colors = {
    "_AbsoluteZero": (0x00, 0x48, 0xBA),
    "_AcidGreen": (0xB0, 0xBF, 0x1A),
    "_AliceBlue": (0xF0, 0xF8, 0xFF),
    "_AlizarinCrimson": (0xE6, 0x1E, 0x63),
    "_Amaranth": (0xE5, 0x2B, 0x50),
    "_Amber": (0xFF, 0xBF, 0x00),
    "_Amethyst": (0x99, 0x66, 0xCC),
    "_AntiFlashWhite": (0xF2, 0xF3, 0xF4),
    "_AntiqueWhite": (0xFA, 0xEB, 0xD7),
    "_Aqua": (0x00, 0xFF, 0xFF),
    "_Aquamarine": (0x7F, 0xFF, 0xD4),
    "_Azure": (0xF0, 0xFF, 0xFF),
    "_AzureishWhite": (0xDB, 0xE9, 0xF4),
    "_BabyBlueEyes": (0xA1, 0xCA, 0xF1),
    "_Beige": (0xF5, 0xF5, 0xDC),
    "_Bisque": (0xFF, 0xE4, 0xC4),
    "_Black": (0x00, 0x00, 0x00),
    "_BlanchedAlmond": (0xFF, 0xEB, 0xCD),
    "_Blue": (0x00, 0x00, 0xFF),
    "_BlueViolet": (0x8A, 0x2B, 0xE2),
    "_BrightPink": (0xFF, 0x00, 0x80),
    "_Brown": (0xA5, 0x2A, 0x2A),
    "_BulgarianRose": (0x4D, 0x19, 0x00),
    "_BurlyWood": (0xDE, 0xB8, 0x87),
    "_Cadet": (0x53, 0x68, 0x72),
    "_CadetBlue": (0x5F, 0x9E, 0xA0),
    "_CadmiumRed": (0xE3, 0x00, 0x22),
    "_CafeAuLait": (0xA6, 0x7B, 0x5B),
    "_Chartreuse": (0x7F, 0xFF, 0x00),
    "_Chocolate": (0xD2, 0x69, 0x1E),
    "_Coral": (0xFF, 0x7F, 0x50),
    "_CornflowerBlue": (0x64, 0x95, 0xED),
    "_Cornsilk": (0xFF, 0xF8, 0xDC),
    "_Crimson": (0xDC, 0x14, 0x3C),
    "_Cyan": (0x00, 0xFF, 0xFF),
    "_DarkBlue": (0x00, 0x00, 0x8B),
    "_DarkBlueGray": (0x66, 0x66, 0x99),
    "_DarkBrown": (0x65, 0x43, 0x21),
    "_DarkCerulean": (0x08, 0x45, 0x7E),
    "_DarkCyan": (0x00, 0x8B, 0x8B),
    "_DarkGoldenrod": (0xB8, 0x86, 0x0B),
    "_DarkGray": (0xA9, 0xA9, 0xA9),
    "_DarkGreen": (0x00, 0x64, 0x00),
    "_DarkKhaki": (0xBD, 0xB7, 0x6B),
    "_DarkLavender": (0x73, 0x4F, 0x96),
    "_DarkMagenta": (0x8B, 0x00, 0x8B),
    "_DarkOliveGreen": (0x55, 0x6B, 0x2F),
    "_DarkOrange": (0xFF, 0x8C, 0x00),
    "_DarkOrchid": (0x99, 0x32, 0xCC),
    "_DarkPowderBlue": (0x00, 0x1E, 0x90),
    "_DarkRed": (0x8B, 0x00, 0x00),
    "_DarkSalmon": (0xE9, 0x96, 0x7A),
    "_DarkSeaGreen": (0x8F, 0xBC, 0x8F),
    "_DarkSlateBlue": (0x48, 0x3D, 0x8B),
    "_DarkSlateGray": (0x2F, 0x4F, 0x4F),
    "_DarkTurquoise": (0x00, 0xCE, 0xD1),
    "_DarkViolet": (0x94, 0x00, 0xD3),
    "_DeepPink": (0xFF, 0x14, 0x93),
    "_DeepSkyBlue": (0x00, 0xBF, 0xFF),
    "_DimGray": (0x69, 0x69, 0x69),
    "_DodgerBlue": (0x1E, 0x90, 0xFF),
    "_ElectricPurple": (0xBF, 0x00, 0xE6),
    "_ElectricBlue": (0x7D, 0xF9, 0xFF),
    "_Firebrick": (0xB2, 0x22, 0x22),
    "_FloralWhite": (0xFF, 0xFA, 0xF0),
    "_ForestGreen": (0x22, 0x8B, 0x22),
    "_Fuchsia": (0xFF, 0x00, 0xFF),
    "_Gainsboro": (0xDC, 0xDC, 0xDC),
    "_GhostWhite": (0xF8, 0xF8, 0xFF),
    "_Glitter": (0xE6, 0xEA, 0xFF),
    "_Gold": (0xFF, 0xD7, 0x00),
    "_Goldenrod": (0xDA, 0xA5, 0x20),
    "_Gray": (0x80, 0x80, 0x80),
    "_Green": (0x00, 0x80, 0x00),
    "_GreenYellow": (0xAD, 0xFF, 0x2F),
    "_Honeydew": (0xE6, 0xFF, 0xF2),
    "_HotPink": (0xFF, 0x69, 0xB4),
    "_IndianRed": (0xCD, 0x5C, 0x5C),
    "_Indigo": (0x4B, 0x00, 0x82),
    "_Ivory": (0xFF, 0xFF, 0xF0),
    "_Khaki": (0xF0, 0xE6, 0x8C),
    "_Lavender": (0xE6, 0xE6, 0xFA),
    "_LavenderBlush": (0xFF, 0xF0, 0xF5),
    "_LawnGreen": (0x7C, 0xFC, 0x00),
    "_LemonChiffon": (0xFF, 0xFA, 0xCD),
    "_LightBlue": (0xAD, 0xD8, 0xE6),
    "_LightCoral": (0xF0, 0x80, 0x80),
    "_LightCyan": (0xE0, 0xFF, 0xFF),
    "_LightGoldenrodYellow": (0xFA, 0xFA, 0xD2),
    "_LightGray": (0xD3, 0xD3, 0xD3),
    "_LightGreen": (0x90, 0xEE, 0x90),
    "_LightPink": (0xFF, 0xB6, 0xC1),
    "_LightSalmon": (0xFF, 0xA0, 0x7A),
    "_LightSeaGreen": (0x20, 0xB2, 0xAA),
    "_LightSkyBlue": (0x87, 0xCE, 0xFA),
    "_LightSlateGray": (0x77, 0x88, 0x99),
    "_LightSteelBlue": (0xB0, 0xC4, 0xDE),
    "_LightYellow": (0xFF, 0xFF, 0xE0),
    "_Lime": (0x00, 0xFF, 0x00),
    "_LimeGreen": (0x32, 0xCD, 0x32),
    "_Linen": (0xFA, 0xF0, 0xE6),
    "_Magenta": (0xFF, 0x00, 0xFF),
    "_Malachite": (0x19, 0xFF, 0x00),
    "_MaroonMust": (0x80, 0x00, 0x00),
    "_MediumAquamarine": (0x66, 0xCD, 0xAA),
    "_MediumBlue": (0x00, 0x00, 0xCD),
    "_MediumOrchid": (0xBA, 0x55, 0xD3),
    "_MediumPurple": (0x93, 0x70, 0xDB),
    "_MediumSeaGreen": (0x3C, 0xB3, 0x71),
    "_MediumSlateBlue": (0x7B, 0x68, 0xEE),
    "_MediumSpringGreen": (0x00, 0xFA, 0x9A),
    "_MediumTurquoise": (0x48, 0xD1, 0xCC),
    "_MediumVioletRed": (0xC7, 0x15, 0x85),
    "_MidnightBlue": (0x19, 0x19, 0x70),
    "_MintCream": (0xF5, 0xFF, 0xFA),
    "_MistyRose": (0xFF, 0xE4, 0xE1),
    "_Moccasin": (0xFF, 0xE4, 0xB5),
    "_Mustard": (0xFF, 0xDB, 0x58),
    "_NavajoWhite": (0xFF, 0xDE, 0xAD),
    "_Navy": (0x00, 0x00, 0x80),
    "_NeonGreen": (0x19, 0xFF, 0x19),
    "_OldLace": (0xFD, 0xF5, 0xE6),
    "_Olive": (0x80, 0x80, 0x00),
    "_OliveDrab": (0x6B, 0x8E, 0x23),
    "_Orange": (0xFF, 0xA5, 0x00),
    "_OrangeRed": (0xFF, 0x45, 0x00),
    "_Orchid": (0xDA, 0x70, 0xD6),
    "_PaleGoldenrod": (0xEE, 0xE8, 0xAA),
    "_PaleGreen": (0x98, 0xFB, 0x98),
    "_PaleTurquoise": (0xAF, 0xEE, 0xEE),
    "_PaleVioletRed": (0xDB, 0x70, 0x93),
    "_PapayaWhip": (0xFF, 0xEF, 0xD5),
    "_PeachPuff": (0xFF, 0xDA, 0xB9),
    "_Peru": (0xCD, 0x85, 0x3F),
    "_Pink": (0xFF, 0xC0, 0xCB),
    "_Plum": (0xDD, 0xA0, 0xDD),
    "_PowderBlue": (0xB0, 0xE0, 0xE6),
    "_Purple": (0x80, 0x00, 0x80),
    "_Red": (0xFF, 0x00, 0x00),
    "_RosyBrown": (0xBC, 0x8F, 0x8F),
    "_RoyalAzure": (0x00, 0x3C, 0xB3),
    "_RoyalBlue": (0x41, 0x69, 0xE1), # web
    "_SaddleBrown": (0x8B, 0x45, 0x13),
    "_Salmon": (0xFA, 0x80, 0x72),
    "_SandyBrown": (0xF4, 0xA4, 0x60),
    "_SeaGreen": (0x2E, 0x8B, 0x57),
    "_SeaShell": (0xFF, 0xF5, 0xEE),
    "_Sienna": (0xA0, 0x52, 0x2D),
    "_Silver": (0xC0, 0xC0, 0xC0),
    "_SkyBlue": (0x87, 0xCE, 0xEB),
    "_SlateBlue": (0x6A, 0x5A, 0xCD),
    "_SlateGray": (0x70, 0x80, 0x90),
    "_Snow": (0xFF, 0xFA, 0xFA),
    "_SpringGreen": (0x00, 0xFF, 0x7F),
    "_SteelBlue": (0x46, 0x82, 0xB4),
    "_Tan": (0xD2, 0xB4, 0x8C),
    "_Tangelo": (0xE6, 0x4C, 0x00),
    "_Teal": (0x00, 0x80, 0x80),
    "_Thistle": (0xD8, 0xBF, 0xD8),
    "_Tomato": (0xFF, 0x63, 0x47),
    "_Turquoise": (0x40, 0xE0, 0xD0),
    "_Violet": (0xEE, 0x82, 0xEE),
    "_Wheat": (0xF5, 0xDE, 0xB3),
    "_White": (0xFF, 0xFF, 0xFF),
    "_WhiteSmoke": (0xF5, 0xF5, 0xF5),
    "_Yellow": (0xFF, 0xFF, 0x00),
    "_YellowGreen": (0x9A, 0xCD, 0x32)
}


def init_provider(presto_obj, rotational_shift=None, scale = None, font = None):
    global WIDTH, HEIGHT
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
        log_debug(f"Setting display scale to {scale}. Was {default_scale}.")
        default_scale = scale

    if font is None:
        pass
    else:
        log_debug(f"Setting display font to {font}. Was {default_font}.")
        default_font = font
    
    vector.set_font(default_font, default_scale)
 
    if rotational_shift is None:
        pass
    else:
        log_debug(f"Setting display rotational shift to {rotational_shift}. Was {default_rotational_shift}.")
        default_rotational_shift = rotational_shift

    WIDTH,HEIGHT = display.get_bounds()
    log_debug(f"Display initialized with width={WIDTH}, height={HEIGHT}, scale={default_scale}, font={default_font}, row_step={row_step}, small_step={small_step}")      

def set_rotational_shift(rotational_shift,y_pos):
    t = picovector.Transform()
    t.rotate(default_rotational_shift,(0,y_pos)) # The corrective "leveling" tilt
    vector.set_transform(t)

def cls(bg=None):
    """
    clear the display

    Args:
        bg: background pen to use

    Returns:
        no return value
    """
    global display, presto
    try:
        if bg is None:
            bg = display.create_pen(0,0,0)

        display.set_pen(bg)
        display.clear()
        presto.update()
    except Exception as e:
        log_debug(f"[cls] {e}")
        presto_errors(f"Error in cls(): {e}")

def translate_color(color_name):
    log_debug("[display_functions] translate_color()")
    try:
        color_dict = Colors[color_name]
        return {"red":color_dict[0],"green":color_dict[1],"blue":color_dict[2] }
    except:
        log_debug(f"Invalid color name: {color_name}. Substituting blue instead.")
        return {"red":0,"green":0,"blue":0}

def set_backlight(brightness,level=0.1):
    try:
        lcl_brightness = brightness + level
        if lcl_brightness < 0:
            lcl_brightness = 0
        elif lcl_brightness > 1:
            lcl_brightness = 1
        presto.set_backlight(lcl_brightness)
        presto.update()
        return lcl_brightness
    except Exception as e:
        log_debug(f"[set_backlight] {e}")
        presto_errors(f"Error in set_backlight(): {e}")

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

    # Set to the passed pen color for drawing the text
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

#def get_color(key):
#    return Colors[key]

def new_pen(color_name):
    pen_color = Colors[color_name]
    return display.create_pen(*pen_color)

def set_pen(pen):
    display.set_pen(pen)

