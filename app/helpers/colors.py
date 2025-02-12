import re
from colorama import Fore, Style, init
init(autoreset=True)

def todo(text):
    p(f'[y]TODO:[c] {text}..')
    exit(2)

# do colors
char2color_map = {
   'b': Fore.BLUE,
   'g': Fore.GREEN,
   'y': Fore.YELLOW,
   'r': Fore.RED,
   'x': Fore.LIGHTBLACK_EX,
   'c': Style.RESET_ALL
}
def p(text, end='\n', flush=False):
    print(z(text), end=end, flush=flush)
def z(text):
    text = str(text)
    for char, color in char2color_map.items():
        text = text.replace('['+char+']', color)
    return text + Style.RESET_ALL
def b(text): return colorize(text, Fore.BLUE)
def g(text): return colorize(text, Fore.GREEN)
def y(text): return colorize(text, Fore.YELLOW)
def r(text): return colorize(text, Fore.RED)
def x(text): return colorize(text, Fore.LIGHTBLACK_EX)
def colorize(char, text): return char2color(char) + text + Style.RESET_ALL
def char2color(char):
    color = char2color_map.get(char)
    if color:
        return color
    raise Exception(z(f'[r]ERROR:char2color():[c] invalid char "{char}"'))
def ln(text):
    return len(remove_colors(text))
def remove_colors(text):
    return re.sub(r'\x1b\[[0-9;]*m', '', z(text))

# align
def ljust(text, width, char=' ', color='c'):
    text_length = len(remove_colors(text))
    if text_length < width:
        color = char2color(color)
        return text + color+(char*(width - text_length))
    return text
def rjust(text, width, char=' ', color='c'):
    text_length = len(remove_colors(text))
    if text_length < width:
        color = char2color(color)
        return color + char*(width - text_length) + '[c]' + text
    return text
def edgesjust(text_left, text_right, width, char=' ', color=False):
    color = char2color(color)
    len_center  = width - len(remove_colors(text_left)) - len(remove_colors(text_right))
    return text_left + (color+len_center*char) + '[c]' + text_right
def center(text, width, char=' ', color='c'):
    text_length = len(remove_colors(text))
    total_padding = width - text_length
    padding_left = total_padding // 2
    padding_right = total_padding - padding_left
    color = char2color(color)
    return (color + char*padding_left) + '[c]' + text + (color + char*padding_right)
