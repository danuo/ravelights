import time

from rich.console import Console
from rich.live import Live
from rich.markup import escape

# console = Console(color_system="truecolor")
console = Console()

string_old = r"""
  _____                 _ _       _     _       
 |  __ \               | (_)     | |   | |      
 | |__) |__ ___   _____| |_  __ _| |__ | |_ ___ 
 |  _  // _` \ \ / / _ \ | |/ _` | '_ \| __/ __|
 | | \ \ (_| |\ V /  __/ | | (_| | | | | |_\__ \
 |_|  \_\__,_| \_/ \___|_|_|\__, |_| |_|\__|___/
                             __/ |              
                            |___/               
"""


string = r"""__________                     __   __        __     __          
\______   \_____ ___  __ ____ |  | |__| ____ |  |___/  |_  ______
 |       _/\__  \\  \/ // __ \|  | |  |/ ___\|  |  \   __\/  ___/
 |    |   \ / __ \\   /\  ___/|  |_|  / /_/  >   Y  \  |  \___ \ 
 |____|_  /(_____/ \_/  \___/ \____/__\___  /|___|  /__| /____  >
        \/                           /_____/      \/  ___ ___ \/ 
                                                 _  _<  // _ \
                                                | |/ / // // /
                                                |___/_(_)___/"""


RAINBOW_COLORS = [
    "rgb(0,10,255)",
    "rgb(61,0,251)",
    "rgb(86,0,247)",
    "rgb(105,0,243)",
    "rgb(120,0,240)",
    "rgb(133,0,236)",
    "rgb(144,0,232)",
    "rgb(154,0,228)",
    "rgb(163,0,225)",
    "rgb(171,0,221)",
    "rgb(179,0,218)",
    "rgb(186,0,215)",
    "rgb(192,0,211)",
    "rgb(198,0,208)",
    "rgb(204,8,205)",
    "rgb(209,20,202)",
    "rgb(214,29,200)",
    "rgb(218,37,197)",
    "rgb(222,45,195)",
    "rgb(226,52,192)",
    "rgb(229,58,190)",
    "rgb(233,65,188)",
    "rgb(236,71,186)",
    "rgb(238,77,184)",
    "rgb(241,83,183)",
    "rgb(243,89,182)",
    "rgb(245,95,180)",
    "rgb(247,101,179)",
    "rgb(249,106,179)",
    "rgb(250,112,178)",
]

RAINBOW_COLORS_REV = RAINBOW_COLORS.copy()
RAINBOW_COLORS_REV.reverse()
RAINBOW_COLORS = RAINBOW_COLORS + RAINBOW_COLORS_REV

start = 0


def new_func(input_text):
    global start
    formatted_text = ""

    start += 10

    for index, char in enumerate(
        input_text,
    ):
        # if char == r"\n":
        # index = 0
        color = RAINBOW_COLORS[(index + start) % len(RAINBOW_COLORS)]
        formatted_text += f"[{color}]{escape(char)}[/]"

    return formatted_text


T = 10
with Live(new_func(string), refresh_per_second=T) as live:
    for _ in range(100):
        time.sleep(1 / T)
        live.update(new_func(string), refresh=True)
