def hex_to_rgb(colour):
    return tuple(int(colour.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

