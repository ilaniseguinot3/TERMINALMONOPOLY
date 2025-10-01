# This file contains the logic for the terminal screen

# Player Terminal total width and height: 153x43. There is 3 extra characters for the border.
# Banker total width and height is 200x60
WIDTH = 150
HEIGHT = 40
INPUTLINE = 45
import os
import utils.networking as net
import platform
import ctypes
import shutil
import re
import keyboard
import time
import textwrap

# Each quadrant is half the width and height of the screen 
global rows, cols
rows = HEIGHT//2
cols = WIDTH//2
DEBUG = False
VERBOSE = True # Set to True to see all output in the output areas. If the user does not need to see the output (any privacy concerns or in a tournament game), set to False via -silent sys.argv.

class OutputArea:
    def __init__(self, name: str, coordinates: tuple, max_length: int, max_lines: int):
        self.name = name
        self.coordinates = coordinates
        self.output_list = []
        self.color_list = []
        self.max_length = max_length
        self.max_lines = max_lines

    def draw(self): # Draw the border and title
        x = self.coordinates[0]
        y = self.coordinates[1]
         # Center name
        for i in range(self.max_lines):
            set_cursor(x,y+1+i)
            print("║" + " " * self.max_length + "║")
        set_cursor(x, y) # Top left
        print("╔" + "═" * self.max_length)  
        set_cursor(x+self.max_length+1,y) # Top left
        print("╗")
        set_cursor(x,y+self.max_lines) # Bottom left
        print("╚" + "═" * self.max_length)
        set_cursor(x+self.max_length+1,y+self.max_lines) # Bottom right
        print("╝")
        name_x = x + self.max_length//2 - len(self.name)//2
        set_cursor(name_x, y)
        print(f" {self.name.upper()} ")

    def add_output(self, output: str, color):
        if VERBOSE:
            msg = textwrap.wrap(output, self.max_length, initial_indent=">> ")
            msg.reverse() # reverse so we can pop from the end and extra wrapped lines are at the end            
            for line in msg:
                self.output_list.insert(0, line)
                self.color_list.insert(0, color)
            while len(self.output_list) > self.max_lines:
                self.output_list.pop()
                self.color_list.pop()
            for i, line in enumerate(self.output_list):
                print(self.color_list[i], end="")
                if "Main" in self.name or "Monopoly" in self.name:
                    if i > self.max_lines-2: # This is the same variable being used, so this keeps everything in bounds. 
                        print(COLORS.RESET, end="", flush=True) # reset color
                        break
                    set_cursor(self.coordinates[0] + 1, self.coordinates[1] + 1 + i) # offset title 
                else:
                    if i >= self.max_lines-2: # This is the same variable being used, so this keeps everything in bounds. 
                        print(COLORS.RESET, end="", flush=True) # reset color
                        break
                    set_cursor(self.coordinates[0] + 1, self.coordinates[1] + 2 + i) # offset title 
                print(line + " " * (self.max_length - len(line)), end="") # print line and clear extra old text
                print(COLORS.RESET, end="", flush=True) # reset color

# Output areas for Banker
Trading_Output = OutputArea(name="Trade Network Output", coordinates=(157, 18), max_length=36, max_lines=17)
Casino_Output = OutputArea("Casino Output", (157, 0), 36, 17)
Monopoly_Game_Output = OutputArea("Monopoly Output", (1, 48), 119, 11)
Main_Output = OutputArea("Main Output", (122, 36), 71, 23)
OUTPUT_AREAS = [Trading_Output, Casino_Output, Monopoly_Game_Output, Main_Output]

class Terminal:
    def __init__(self, index: int, coordinates: tuple):
        self.index = index
        self.x = coordinates[0] # top left corner of the terminal
        self.y = coordinates[1] # top left corner of the terminal
        self.data = []
        self.command = ""
        self.padded_data = False
        self.status = "ACTIVE"
        self.persistent = False
        self.has_new_data = False
        self.oof_callable = None

    def update(self, data, padding: bool = True) -> None:
        """
        Description:
            Better quadrant update function.
            This exceeds others because it immediately updates a single quadrant with the new data.
            Previously, the screen would not update until print_screen() was called.
            Furthermore, print_screen() would overwrite the entire screen, which is not ideal and slower.\n
            Set padding = True if you're not sure whether your module needs padding.
        
        Parameters: 
            data (str): The string (with newlines to separate lines) to populate the quadrant with.
            data (function): A function that populates the quadrant manually. Useful for modules that need 
                to print with colors or other formatting
            padding (bool): (default True) a flag whether or not your module needs extra padding 
                    (blank spaces) to fill in any missing lines
        Returns: 
            None
        """

        self.padded_data = padding

        # These lines are taking any additional string fragments that use "set_cursor_string()" from 
        # style.py and update the x,y coordinates to the current quadrant.
        self.data = self.translate_coords(data)
        self.display()
    
    def check_new_data(self, new_data: str):
        """
        Only checks if the new data is different from the old data. If it is, it updates the data and sets has_new_data to True.
        This will later be used to determine if the terminal needs to be redrawn, saving unnecessary print statements.
        """
        if self.data != new_data:
            self.data = new_data
            self.has_new_data = True
        else:
            self.has_new_data = False

    def display(self) -> None:
        """
        Description:
            Prints the terminal data defined in its internal data variable.
        
        Parameters: 
            None
        Returns: 
            None
        """
        print(COLORS.RESET, end='') # Reset color before printing
        if self.data and not callable(self.data):
            if self.data:
                line_list = self.data.split('\n')
                if len(line_list) > rows and self.padded_data:
                    line_list = line_list[:rows] # Truncate if necessary bc someone might send a long string
                for i in range(len(line_list)):
                    set_cursor(self.x,self.y+i)
                    if self.padded_data: 
                        line_list[i] = line_list[i] + " " * (cols - len(line_list[i])) # Pad with spaces if necessary

                    print(line_list[i][:cols] if len(line_list[i]) > cols and self.padded_data else line_list[i]) # Truncate if necessary bc someone might send a long string
                for i in range(len(line_list), rows):
                    set_cursor(self.x,self.y+i)
                    print(" " * cols)
        elif callable(self.data):
            self.data()
        else:
            set_cursor(x=self.x + 10, y= self.y + 4)
            print(f'╔══════Terminal {self.index}══════╗')
            
            set_cursor(x=self.x + 10, y= self.y + 5)
            print('║ Awaiting commands... ║')

            set_cursor(x=self.x + 10, y= self.y + 6)
            print('╚══════════════════════╝')

        debug_note()
        print(COLORS.RESET, end='')
        set_cursor(0,INPUTLINE)
    
    def translate_coords(self, data) -> str:
        pattern = r'\033\[(\d+);(\d+)H'
        data = re.sub(pattern, lambda m: replace_sequence(m, self.x, self.y), data)
        return data

    def clear(self):
        """Prints a blank screen in the terminal."""
        for i in range(rows):
            set_cursor(self.x,self.y+i)
            print(" " * cols)

    def kill(self):
        """
        Description:
            Kills a terminal, triggered by a netcommand.
        Parameters: 
            None
        Returns: 
            None
        """
        self.status = "DISABLED"
        skull = g.get("skull")
        print(COLORS.RED)
        self.update(skull)
        print(COLORS.RESET)
        set_cursor(0, INPUTLINE)

    def disable(self):
        """
        Description:
            Disables a terminal, triggered by a netcommand.
        Parameters: 
            None
        Returns: 
            None
        """
        self.status = "DISABLED"
        print(COLORS.RED)
        result = (('X ' * round(cols/2+0.5) + '\n' + 
                (' X' * round(cols/2+0.5)) + '\n'
                ) * (rows//2))
        self.update(result)
        print(COLORS.RESET)
        set_cursor(0, INPUTLINE)

    def enable(self, isFromDisable, socket, player_id):
        """
        Description:
            Enables a terminal, triggered either by the client or by a netcommand.
        Parameters: 
            isFromDisable(bool): Whether it is triggered from a disable.
            socket(socket): The socket to update the banker's statuses.
            player_id(int): The player's ID for the message send.
        Returns: 
            None
        """
        self.status = "ACTIVE"
        net.send_message(socket, str(player_id) + "active " + str(self.index))
        if(isFromDisable):
            self.update("This terminal is now enabled!")
    
    def busy(self, socket, player_id):
        """
        Description:
            Busies a terminal.
        Parameters: 
            socket(socket): The socket to update the banker's statuses.
            player_id(int): The player's ID for the message send.
        Returns:
            None
        """
        self.status = "BUSY"
        net.send_message(socket, str(player_id) + "busy " + str(self.index))

    def change_border_color(self, c):
        """
        Changes the border color of a terminal. Very handy.
        """
        border_chars = [('╔','╦','╠','╬'),
                        ('╦','╗','╬','╣'),
                        ('╠','╬','╚','╩'),
                        ('╬','╣','╩','╝')]
        
        t = self.index - 1
        set_cursor(self.x-1,self.y-1)
        print(c, end='')
        print(border_chars[t][0] + '═' * cols + border_chars[t][1], end='')
        set_cursor(self.x-1,self.y+rows)
        print(border_chars[t][2] + '═' * cols + border_chars[t][3], end='')
        for i in range(self.y, self.y + rows):
            set_cursor(self.x-1, i)
            print('║')
            set_cursor(self.x+cols, i)
            print('║')

    def indicate_keyboard_hook(self, off=False):
        """
        Indicates that the keyboard hook is active for a certain terminal. 
        Changes the color of the terminal border.
        This is important for the player to know why they can't type on the input line.
        """
        if off:
            c = COLORS.GREEN
        else:
            c = COLORS.LIGHTBLUE

        self.change_border_color(c)


def notification(message: str, n: int, color: str, custom_x: int, custom_y: int) -> str:
    """
    Generates a notification popup message for the player.
    Parameters:
        message (str): The message to be displayed in the notification.
        n (int): The position identifier for the popup. 
                 1 - Top-left, 2 - Top-right, 3 - Bottom-left, 4 - Bottom-right, -1 - Custom position.
        color (str): The color code for the popup text.
    Returns:
        str: The formatted string with the notification message and its position.
    """
    # Max 78 character popup for messaging the player.
    message = message + " " * max(0, (78 - len(message)))
    lines = textwrap.wrap(message, 78/3)
    x,y = -1,-1
    writeto = ""
    if (n == 1):
        x,y = 2+10,2+5
    elif (n == 2):
        x,y = cols+3+10, 2+5
    elif (n == 3):
        x,y = 2+10, rows+3+5
    elif (n == 4):
        x,y = cols+3+10, rows+3+5
    elif (n == -1):
        x,y = cols - 20, rows - 5
        if custom_x and custom_y:
            x = custom_x
            y = custom_y

    p = color + set_cursor_str(x, y)
    outline = g["popup 1"].split("\n")
    for i in range(len(outline)):
        p += set_cursor_str(x, y+i) + outline[i]
        if 0 < i < 4:
            # Custom text wrapping
            p += set_cursor_str(x+2, y+i) + message[(i-1)*26:(i-1)*26+26]
    writeto += p
    return writeto + set_cursor_str(0, INPUTLINE)

def replace_sequence(match, x, y):
    """
    Replaces the x and y coordinates in the matched string with the new x and y coordinates.
    Useful when updating the cursor position in a string, allowing for set_cursor_str() to 
    be used in any quadrant.
    """
    # Extract the number N from the matched string
    nx = int(match.group(2))
    ny = int(match.group(1))

    # Calculate the new x and y coordinates
    new_x = nx + x
    new_y = ny + y
    # Return the new sequence
    return f"\033[{new_y};{new_x}H"

def update_terminal(n: int, o: int): # TODO not working at the moment
    """
    Updates the terminal border to indicate the active terminal. Turns off the border for the inactive terminal.
    """
    x,y = -1,-1
    border_chars = [('╔','╦','╠','╬'),
                    ('╦','╗','╬','╣'),
                    ('╠','╬','╚','╩'),
                    ('╬','╣','╩','╝')]
    if type(o) == Terminal:
        o = o.index    

    if (o == 1):
        x,y = 0,1
    elif(o == 2):
        x,y = cols+2, 1
    elif(o == 3):
        x,y = 0, rows+2
    elif(o == 4):
        x,y = cols+2, rows+2
    o = o - 1 # 0-indexed
    c = COLORS.LIGHTGRAY
    set_cursor(x,y)
    print(c, end='')
    print(border_chars[o][0] + '═' * cols + border_chars[o][1], end='')
    set_cursor(x,y+rows+1)
    print(border_chars[o][2] + '═' * cols + border_chars[o][3], end='')
    for i in range(y, y + rows):
        set_cursor(x, i+1)
        print('║')
        set_cursor(x+cols + (1 if (o + 1) % 2 == 0 else 2), i+1)
        print('║')

    if (n == 1):
        x,y = 0,1
    elif (n == 2):
        x,y = cols+2, 1
    elif (n == 3):
        x,y = 0, rows+2
    elif (n == 4):
        x,y = cols+2, rows+2
    n = n - 1 # 0-indexed
    c = COLORS.GREEN

    set_cursor(x,y)
    print(c, end='')
    print(border_chars[n][0] + '═' * cols + border_chars[n][1], end='')
    set_cursor(x,y+rows+1)
    print(border_chars[n][2] + '═' * cols + border_chars[n][3], end='')
    for i in range(y, y + rows):
        set_cursor(x, i+1)
        print('║')
        set_cursor(x+cols + (1 if (n + 1) % 2 == 0 else 2), i+1)
        print('║')
    
    set_cursor(0,INPUTLINE)
    print(COLORS.RESET, end='')

    debug_note()

def debug_note():
    if DEBUG:
        message = 'DEBUG MODE'
        set_cursor(WIDTH-10-len(message),0)
        print(f'{COLORS.GREEN}{message}{COLORS.RESET}')
        set_cursor(0,INPUTLINE)

def overwrite(text: str = ""):
    """
    Writes text over 2nd to last line of the terminal (input line).
    
    Use this method regularly.
    
    Parameters: 
    text (str): The text to overwrite with. Default is empty string.

    Returns: None
    """
    set_cursor(0, INPUTLINE)
    print(f'\033[1A\r{COLORS.RESET}{text}', end=' ' * (WIDTH - len(text) + 3) + '\n' + ' ' * (WIDTH + 3) + '\r' + COLORS.RESET)
    set_cursor(0, INPUTLINE)

def get_valid_int(prompt, min_val = -1000000000, max_val = 1000000000, disallowed = [], allowed = []): # arbitrary large numbers
    """
    Prompts the user to enter an integer within a specified range and validates the input.
    Parameters:
        prompt (str): The message displayed to the user when asking for input.
        min_val (int, optional): The minimum acceptable value (inclusive). Defaults to -1000000000.
        max_val (int, optional): The maximum acceptable value (inclusive). Defaults to 1000000000.
        disallowed (list, optional): A list of disallowed values. Defaults to an empty list.
        allowed (list, optional): A list of allowed values. Defaults to an empty list. 
            If a space is in the whitelist, user is allowed to skip input (enter key), returning an empty string.
    Returns:
        int: A valid integer input by the user within the specified range. (or an empty string if allowed)
    Raises:
        None: All exceptions are caught and handled by the function.
    """
    while True:
        try:
            set_cursor(0, INPUTLINE)
            value = int(input(prompt))
            if value in allowed:
                return value
            if value < min_val or value > max_val or value in disallowed:
                raise ValueError
            return value
        except ValueError:
            try:
                value # check if value is defined. If not, the input was empty and the user pressed enter.
            except UnboundLocalError:
                if " " in allowed:
                    return "" # This is the signal to skip input
            overwrite("Invalid input. Please enter a valid integer.")
            set_cursor(0, INPUTLINE)

def clear_screen():
    """
    Naively clears the terminal screen.

    Parameters: None
    Returns: None
    """
    print(COLORS.RESET,end='')
    os.system('cls' if os.name == 'nt' else 'clear')

def initialize_terminals(terminals: list[Terminal]):
    """
    Initializes the terminal screen with the default number displays and terminal borders.
    """
    clear_screen()
    print(g.get('terminals'))
    for i in range(4):
        terminals[i].update('')
    set_cursor(0,INPUTLINE)

def make_fullscreen():
    current_os = platform.system()

    if current_os == "Windows":
        # Maximize terminal on Windows
        user32 = ctypes.WinDLL("user32")
        SW_MAXIMIZE = 3
        hWnd = user32.GetForegroundWindow()
        user32.ShowWindow(hWnd, SW_MAXIMIZE)

    elif current_os == "Linux" or current_os == "Darwin":
        # Maximize terminal on Linux/macOS
        os.system("printf '\033[9;1t'")
    else:
        print(f"Fullscreen not supported for OS: {current_os}")

def print_with_wrap(char, start_row, start_col):
    # Get the terminal size
    terminal_size = shutil.get_terminal_size()
    width = terminal_size.columns
    
    # If the position exceeds the terminal width, handle wrapping
    if start_col >= width:
        # Calculate new row and column if it exceeds width
        new_row = start_row + (start_col // width)
        new_col = start_col % width
        print(f"\033[{new_row};{new_col}H" + char, end="")
    else:
        # Default print
        print(f"\033[{start_row};{start_col}H" + char, end="")

def calibrate_print_commands():
    """
    Print commands, used in calibration screen.\n
    """
    commandsinfo = g.get('commands').split("\n")
    for i in range(len(commandsinfo)):
        for j in range(len(commandsinfo[i])):
            print(f"\033[{34+i};79H" + commandsinfo[i][:j], end="")

def print_banker_frames():
    """
    Prints the banker frames.
    
    Parameters: None
    Returns: None
    """
    gameboard = g.get('gameboard')
    border = g.get('history and status').split('\n')
    history = []
    set_cursor(0,0)
    print(gameboard)
    for i in range(len(border)):
        set_cursor(79,i)
        if(len(history) - i<= 0):
            for j in range(len(border[i])):
                print(border[i][j], end="")
    calibrate_print_commands()        
    for OA in OUTPUT_AREAS:
        OA.draw()
    # casino_frame = g.get('casino_output_frame')
    # i = 0
    # for line in casino_frame.split('\n'):
    #     set_cursor(CASINO_OUTPUT_COORDINATES[0], CASINO_OUTPUT_COORDINATES[1]+i)
    #     print(line, end="")
    #     i += 1
    # i -= 1
    # ttt_frame = g.get('ttt_output_frame')
    # for line in ttt_frame.split('\n'):
    #     set_cursor(TTT_OUTPUT_COORDINATES[0], i)
    #     print(line, end="")
    #     i += 1
    # monopoly_output_frame = g.get('monopoly_output_frame')
    # i = 0
    # for line in monopoly_output_frame.split('\n'):
    #     set_cursor(MONOPOLY_OUTPUT_COORDINATES[0], MONOPOLY_OUTPUT_COORDINATES[1]+i)
    #     print(line, end="")
    #     i += 1

def auto_calibrate_screen(mode: str = "player") -> None:
    """
    Automatically calibrates the screen. The player doesn't really know what screen size is 
    optimal, but we do. This function will automatically adjust the screen size to the ensure 
    minimum requirements are met.
    """
    if mode == "player":
        if os.name == 'nt': # Windows
            max_iterations = 20
            while os.get_terminal_size().lines - 5 < HEIGHT or os.get_terminal_size().columns - 5 < WIDTH:
                keyboard.press('ctrl')
                keyboard.send('-')
                keyboard.release('ctrl')
                time.sleep(0.1)
                max_iterations -= 1
                if max_iterations <= 0:
                    break
            max_iterations = 20
            while os.get_terminal_size().lines > HEIGHT + 40 or os.get_terminal_size().columns > WIDTH + 40:
                keyboard.press('ctrl')
                keyboard.send('+')
                keyboard.release('ctrl')
                time.sleep(0.1)
                max_iterations -= 1
                if max_iterations <= 0:
                    break
        elif os.name == 'posix': # Linux/macOS
            print("\033[8;50;160t") # Set terminal size to 50 rows and 160 columns
    elif mode == "banker":
        if os.name == 'nt': # Windows
            
            max_iterations = 20 # Safeguard to prevent infinite loop due to user error or logic error
            while os.get_terminal_size().lines - 5 < 60 or os.get_terminal_size().columns - 5 < 200:
                keyboard.press('ctrl')
                keyboard.send('-')
                keyboard.release('ctrl')
                time.sleep(0.1)
                max_iterations -= 1
                if max_iterations <= 0:
                    break

            max_iterations = 20
            while os.get_terminal_size().lines > 60 + 20 or os.get_terminal_size().columns > 200 + 20:
                keyboard.press('ctrl')
                keyboard.send('+')
                keyboard.release('ctrl')
                time.sleep(0.1)
                max_iterations -= 1
                if max_iterations <= 0:
                    break

        elif os.name == 'posix': # Linux/macOS
            print("\033[8;60;200t") # Set terminal size to 60 rows and 200 columns

def calibrate_screen(type: str) -> None:
    terminal_size = shutil.get_terminal_size()
    width = terminal_size.columns
    os.system('cls' if os.name == 'nt' else 'clear')
    current_os = platform.system()

    colortest()    
    choice = input("How does this look? Enter the number of your preferred colorset: ")

    # sets the color set based on user input
    global COLORS
    if choice == "1":
        print("Using default colorset")
        choose_colorset("DEFAULT_COLORS")
    elif choice == "2":
        print("Using compatible colorset")
        choose_colorset("COMPAT_COLORS")
    elif choice == "3":
        print("Using custom colorset")
        choose_colorset("CRAZY_THEME")
    else:
        print("Please enter a valid choice")
        choose_colorset("DEFAULT_COLORS") # default to default colorset
    input("Press enter to continue...")

    clear_screen()
    print("Character set test. If characters are not displaying correctly, please change your terminal font to a monospace font.\n")
    print("If you are using Windows, please use the 'Consolas' font.\n")
    print("If you are using Linux, please use the 'DejaVu Sans Mono' font.\n")
    print("If you are using macOS, please use the 'Menlo' font.\n")
    print("In addition, please ensure that your terminal is set to use UTF-8 encoding.\n")
    print("If you are using Windows, please use the 'Terminal' application.\n")
    print("If you are using Linux, please use the 'Gnome Terminal' application.\n")
    print("If you are using macOS, please use the 'Terminal' application.\n")
    print(g.get('.chartest'))

    c = input("\n\nIf none of the above options work, type 1 to submit an issue on GitHub, or press enter to continue.\n")
    if c == "1":
        clear_screen()
        print("If you are using a different terminal, please let us know and we will try to add support for it.")
        print("Please submit an issue on GitHub at \n https://github.com/ufosc/TERMINALMONOPOLY/issues \nwith the details of your terminal and OS.")
        print("Include the following information:\n")
        print(f"Operating System: {platform.system()} {platform.release()} ({platform.version()})")
        print(f"Terminal Type: {os.name}")
        print(f"Terminal Name: {os.getenv('TERM', 'Unknown')}")
        print(f"Terminal Size: {shutil.get_terminal_size().columns}x{shutil.get_terminal_size().lines}")
        print(f"Python Version: {platform.python_version()}")
        print(f"Terminal Encoding: {os.device_encoding(1) or 'Unknown'}")
        print("Please include a screenshot of the terminal with the issue.")

        input("Press enter to continue...")

    clear_screen()

    if current_os == "Darwin":
        # Print out instructions for macOS users
        print("Please use Ctrl + \"Command\" + \"+\" or Ctrl + \"Command\" + \"-\" to zoom in/out and ensure everything is visible. Press enter to continue to scaling screen.")
    else:
        # Print out instructions for Linux/Windows users
        print("Please use \"Ctrl\" + \"-\" or \"Ctrl\" + \"+\" to zoom in/out and ensure everything is visible. Press enter to continue to scaling screen.")
    print("Proper scaling should only displays 4 cross that marks the corners of the board.")
    print("If you are having trouble with scaling, try entering r to reset the display.")
    print("After finishing scaling, please press enter to continue.")
    scaling_test = input()
    os.system('cls' if os.name == 'nt' else 'clear')
    if type == "gameboard":
        gameboard = g.get('gameboard')
        border = g.get('history and status').split('\n')
        history = []
        print(f"\033[0;0H" + gameboard, end="")
        for i in range(len(border)):
            print(f"\033[{i};79H", end="")
            if(len(history) - i<= 0):
                for j in range(len(border[i])):
                    print(border[i][j], end="")
        calibrate_print_commands()
        print_with_wrap("X", 0, 0)
        print_with_wrap("X", 0, 156)
        print_with_wrap("X", 50, 156)
        print_with_wrap("X", 50, 0)
        print(f"\033[36;0H" + "Press enter to play or enter r to reset the display.", end="")
        scaling_test = input()
        while scaling_test != "":
            if scaling_test == "r":
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"\033[0;0H" + gameboard, end="")
                for i in range(len(border)):
                    print(f"\033[{i};79H", end="")
                    if(len(history) - i<= 0):
                        for j in range(len(border[i])):
                            print(border[i][j], end="")
                calibrate_print_commands()
                print_with_wrap("X", 0, 0)
                print_with_wrap("X", 0, 156)
                print_with_wrap("X", 50, 156)
                print_with_wrap("X", 50, 0)
                print(f"\033[36;0H" + "Press enter to play or enter r to reset the display.", end="")
            scaling_test = input()
    elif type == "player":
        os.system('cls' if os.name == 'nt' else 'clear')
        set_cursor(0,0)
        print(g.get('terminals'))
        print_with_wrap("X", 0, 0)
        print_with_wrap("X", 0, 153)
        print_with_wrap("X", 43, 153)
        print_with_wrap("X", 43, 0)
        print(f"\033[44;0H" + "Press enter to play or enter r to reset the display.", end="")
        scaling_test = input()
        while scaling_test != "":
            os.system('cls' if os.name == 'nt' else 'clear')
            set_cursor(0,0)
            print(g.get('terminals'))
            print_with_wrap("X", 0, 0)
            print_with_wrap("X", 0, 153)
            print_with_wrap("X", 43, 153)
            print_with_wrap("X", 43, 0)
            print(f"\033[44;0H" + "Press enter to play or enter r to reset the display.", end="")
            scaling_test = input()
        os.system('cls' if os.name == 'nt' else 'clear')
    elif type == "banker": # gameboard is least 156 characters, but we need extra space for additional output for debugging purposes (40 chars)
        # Total banker display is 60 rows x 200 columns. Default screen size usually will not accomodate, so use calibration here
        os.system('cls' if os.name == 'nt' else 'clear')
        
        def print_xs():
            print_with_wrap("X", 0, 0)
            print_with_wrap("X", 0, 200)
            print_with_wrap("X", 59, 0)
            print_with_wrap("X", 59, 200)
            print(f"\033[60;0H" + "Press enter to play or enter r to reset the display.", end="")

        print_banker_frames()
        auto_calibrate_screen("banker")
        print_xs()
        scaling_test = input()
        while scaling_test != "":
            os.system('cls' if os.name == 'nt' else 'clear')
            print_banker_frames()
            print_xs()
            scaling_test = input()
        os.system('cls' if os.name == 'nt' else 'clear')


class COMPAT_COLORS:
    description = textwrap.wrap("A set of colors that are compatible with most terminals.", width=30,
                                initial_indent="> ", subsequent_indent=" ")
    BROWN = "\033[38;5;94m"
    LIGHTBLUE = "\033[38;5;33m"
    ROUGE = "\033[38;5;13m"
    ORANGE = "\033[38;5;208m"

    # https://en.wikipedia.org/wiki/ANSI_escape_code#8-bit
    # Uses Standard colors (0-7) and High-Intensity colors (8-15) from 8-bit ANSI escape codes
    RED = "\033[38;5;1m"
    YELLOW = "\033[38;5;11m"
    GREEN = "\033[38;5;10m"
    BLUE = "\033[38;5;4m"
    WHITE = "\033[38;5;15m"
    CYAN = "\033[38;5;14m"
    LIGHTGRAY = "\033[38;5;247m"
    LIGHTBLACK = "\033[38;5;8m"
    CHANCE = "\033[38;5;214m"
    COMMUNITY = "\033[38;5;45m"
    BLACK = "\033[38;5;0m"

    # Reset color
    RESET = "\033[0m"
    # Player colors: red, green, yellow, blue, respectively
    playerColors = ["\033[38;5;1m", "\033[38;5;2m", "\033[38;5;3m", "\033[38;5;4m"]
    # display colors are used for printing text in Terminal, like error messages, etc. Not to be used on gameboard.
    dispGREEN = "\033[38;5;2m"
    dispRED = "\033[38;5;9m"
    dispBLUE = "\033[38;5;12m"

    backBROWN = BROWN.replace("38", "48")
    backLIGHTBLUE = LIGHTBLUE.replace("38", "48")
    backROUGE = ROUGE.replace("38", "48")
    backORANGE = ORANGE.replace("38", "48")
    backRED = RED.replace("38", "48")
    backYELLOW = YELLOW.replace("38", "48")
    backGREEN = GREEN.replace("38", "48")
    backBLUE = BLUE.replace("38", "48")
    backWHITE = WHITE.replace("38", "48")
    backCYAN = CYAN.replace("38", "48")
    backLIGHTGRAY = LIGHTGRAY.replace("38", "48")
    backLIGHTBLACK = LIGHTBLACK.replace("38", "48")
    backCHANCE = CHANCE.replace("38", "48")
    backCOMMUNITY = COMMUNITY.replace("38", "48")
    backBLACK = BLACK.replace("38", "48")


class DEFAULT_COLORS:
    description = textwrap.wrap("The default TERMINAL MONOPOLY experience.", width=30, initial_indent="> ",
                                subsequent_indent=" ")
    BROWN = "\033[38;2;138;96;25m"
    LIGHTBLUE = "\033[38;2;43;249;255m"
    ROUGE = "\033[38;2;240;93;231m"
    ORANGE = "\033[38;2;246;160;62m"
    RED = "\033[38;2;246;62;62m"
    YELLOW = "\033[38;2;240;255;91m"
    GREEN = "\033[38;2;41;129;32m"
    BLUE = "\033[38;2;44;37;255m"
    WHITE = "\033[38;2;255;255;255m"
    CYAN = "\033[38;2;0;255;239m"
    LIGHTGRAY = "\033[38;2;193;193;193m"
    LIGHTBLACK = "\033[38;2;88;88;88m"
    CHANCE = "\033[38;2;255;191;105m"
    COMMUNITY = "\033[38;2;0;137;255m"
    BLACK = "\033[38;5;0m"

    # Reset color
    RESET = "\033[0m"
    # Player colors: red, green, yellow, blue, respectively
    playerColors = ["\033[38;5;1m", "\033[38;5;2m", "\033[38;5;3m", "\033[38;5;4m"]
    # display colors are used for printing text in Terminal, like error messages, etc. Not to be used on gameboard.
    dispGREEN = "\033[38;5;2m"
    dispRED = "\033[38;5;9m"
    dispBLUE = "\033[38;5;12m"

    backBROWN = BROWN.replace("38", "48")
    backLIGHTBLUE = LIGHTBLUE.replace("38", "48")
    backROUGE = ROUGE.replace("38", "48")
    backORANGE = ORANGE.replace("38", "48")
    backRED = RED.replace("38", "48")
    backYELLOW = YELLOW.replace("38", "48")
    backGREEN = GREEN.replace("38", "48")
    backBLUE = BLUE.replace("38", "48")
    backWHITE = WHITE.replace("38", "48")
    backCYAN = CYAN.replace("38", "48")
    backLIGHTGRAY = LIGHTGRAY.replace("38", "48")
    backLIGHTBLACK = LIGHTBLACK.replace("38", "48")
    backCHANCE = CHANCE.replace("38", "48")
    backCOMMUNITY = COMMUNITY.replace("38", "48")
    backBLACK = BLACK.replace("38", "48")


class CRAZY_THEME:
    description = textwrap.wrap("A bold colorset.", width=30, initial_indent="> ", subsequent_indent=" ")
    fore_prefix = "\033[38;2;"
    back_prefix = "\033[48;2;"
    BROWN = fore_prefix + "169;0;196m"
    LIGHTBLUE = fore_prefix + "157;255;254m"
    ROUGE = fore_prefix + "239;180;255m"
    ORANGE = fore_prefix + "255;115;0m"
    RED = fore_prefix + "204;17;17m"
    YELLOW = fore_prefix + "206;255;42m"
    GREEN = fore_prefix + "56;255;250m"
    BLUE = fore_prefix + "0;20;110m"
    WHITE = fore_prefix + "254;229;255m"
    CYAN = fore_prefix + "158;254;255m"
    LIGHTGRAY = fore_prefix + "220;181;255m"
    LIGHTBLACK = fore_prefix + "118;78;78m"
    CHANCE = fore_prefix + "228;59;135m"
    COMMUNITY = fore_prefix + "13;151;19m"
    BLACK = fore_prefix + "39;76;79m"
    RESET = "\033[0m"
    playerColors = ["\033[38;5;1m", "\033[38;5;2m", "\033[38;5;3m", "\033[38;5;4m"]
    dispGREEN = fore_prefix + "245;0;255m"
    dispRED = fore_prefix + "7;0;255m"
    dispBLUE = fore_prefix + "255;251;0m"
    backBROWN = back_prefix + "132;25;25m"
    backLIGHTBLUE = back_prefix + "215;127;132m"
    backROUGE = back_prefix + "132;25;130m"
    backORANGE = back_prefix + "132;93;25m"
    backRED = back_prefix + "132;25;25m"
    backYELLOW = back_prefix + "126;132;25m"
    backGREEN = back_prefix + "41;132;25m"
    backBLUE = back_prefix + "25;27;132m"
    backWHITE = back_prefix + "255;244;205m"
    backCYAN = back_prefix + "49;98;98m"
    backLIGHTGRAY = back_prefix + "133;133;133m"
    backLIGHTBLACK = back_prefix + "78;78;78m"
    backCHANCE = back_prefix + "136;186;234m"
    backCOMMUNITY = back_prefix + "210;208;38m"
    backBLACK = back_prefix + "38;38;38m"


class MYCOLORS:
    description = textwrap.wrap("This is the colorset the player chooses to use in the game.", width=30,
                                initial_indent="> ", subsequent_indent=" ")
    BROWN = ""
    LIGHTBLUE = ""
    ROUGE = ""
    ORANGE = ""
    RED = ""
    YELLOW = ""
    GREEN = ""
    BLUE = ""
    WHITE = ""
    CYAN = ""
    LIGHTGRAY = ""
    LIGHTBLACK = ""
    CHANCE = ""
    COMMUNITY = ""
    BLACK = ""
    RESET = ""
    playerColors = ["", "", "", ""]
    dispGREEN = ""
    dispRED = ""
    dispBLUE = ""
    backBROWN = ""
    backLIGHTBLUE = ""
    backROUGE = ""
    backORANGE = ""
    backRED = ""
    backYELLOW = ""
    backGREEN = ""
    backBLUE = ""
    backWHITE = ""
    backCYAN = ""
    backLIGHTGRAY = ""
    backLIGHTBLACK = ""
    backCHANCE = ""
    backCOMMUNITY = ""
    backBLACK = ""


def choose_colorset(colorset: str) -> None:
    """
    This function sets the colorset for the game. It takes a string as an argument, which is the name of the colorset.
    It then sets the colorset to the chosen colorset, and sets the background colors to the chosen colorset.
    Parameters:
    colorset (str): The name of the colorset to be used.
    Returns:
    None
    """
    global MYCOLORS
    if colorset == "COMPAT_COLORS":
        # Set the colorset to the compatible colors
        for attr in dir(COMPAT_COLORS):
            if not attr.startswith('__'):
                setattr(MYCOLORS, attr, getattr(COMPAT_COLORS, attr))

    elif colorset == "DEFAULT_COLORS":
        # Set the colorset to the default defined colors
        for attr in dir(DEFAULT_COLORS):
            if not attr.startswith('__'):
                setattr(MYCOLORS, attr, getattr(DEFAULT_COLORS, attr))
    elif colorset == "CRAZY_THEME":
        # Set the colorset to the crazy theme colors
        for attr in dir(CRAZY_THEME):
            if not attr.startswith('__'):
                setattr(MYCOLORS, attr, getattr(CRAZY_THEME, attr))

    else:
        raise ValueError("Invalid colorset. Please choose either 'COMPAT_COLORS' or 'DEFAULT_COLORS'.")


def colortest():
    """
    Prints a test of all colors defined in the COLORS class.
    """
    set_cursor(1, 4)
    print(g.get("colortestboundary"))
    y = 7
    for color in dir(MYCOLORS):
        if not color.startswith('__') and color != "back_prefix" and not color.startswith(
                'back') and color != "RESET" and color != "description" and color != "fore_prefix":
            value = getattr(MYCOLORS, color)
            if isinstance(value, list):
                for item in value:
                    set_cursor(2, y)
                    print(item + f"█████ {color}" + MYCOLORS.RESET)
                    y += 1
            else:
                set_cursor(2, y)
                print(value + f"█████ {color}" + MYCOLORS.RESET)
                y += 1
            set_cursor(2, y)

    y = y + 1
    for color in dir(MYCOLORS):
        if color.startswith('back'):
            value = getattr(MYCOLORS, color)
            set_cursor(2, y)
            print(value + f"      {color}" + MYCOLORS.RESET)
            y += 1

    print(COMPAT_COLORS.WHITE, end="")  # Reset foreground to white for better visibility

    sets = [DEFAULT_COLORS, COMPAT_COLORS, CRAZY_THEME]  # Add to this list to add more color sets to the test.

    offset = max([len(sets[x].description) for x in range(len(sets))]) + 1

    for x in range(len(sets)):
        x_offset = 31
        y = 0
        set_cursor(x * x_offset + x_offset, y)
        lines = textwrap.wrap(f"Testing color set {sets[x].__name__}:", width=x_offset)
        for line in lines:
            set_cursor(x * x_offset + x_offset, y + 1)
            print(line, end="")
            y += 1
        j = 0
        for line in sets[x].description:
            set_cursor(x * x_offset + x_offset, y + 1 + j)
            print(line, end="")
            j += 1
        y = offset
        set_cursor(x * x_offset + x_offset, y + 2)
        print("Testing foreground colors:\n")
        for color in dir(sets[x]):
            if not color.startswith('__') and color != "back_prefix" and not color.startswith(
                    'back') and color != "RESET" and color != "description" and color != "fore_prefix":
                value = getattr(sets[x], color)
                if isinstance(value, list):  # Special case for playerColors
                    for item in value:
                        set_cursor(x * x_offset + x_offset, y + 3)
                        print(item + f"█████ {color}" + sets[x].RESET)
                        y += 1
                else:
                    set_cursor(x * x_offset + x_offset, y + 3)
                    print(value + f"█████ {color}" + sets[x].RESET)
                    y += 1

        print(COMPAT_COLORS.WHITE, end="")  # Reset foreground to white for better visibility
        set_cursor(x * x_offset + x_offset, y + 3)
        print("Testing background colors:")
        for color in dir(sets[x]):
            print(COMPAT_COLORS.WHITE, end="")  # Reset foreground to white for better visibility
            if color.startswith('back'):
                value = getattr(sets[x], color)
                set_cursor(x * x_offset + x_offset, y + 4)
                print(value + f"      {color}" + sets[x].RESET)
                y += 1


def print_w_dots(text: str, size: int = 50, end: str = '\n') -> None:
    """
    Prints a green string with predetermined dot padding after it.

    Parameters:
    text (str): string to pad dots after.
    size (int): integer of how long the padded string should be. Default 50.
    end (str): value to print immediately at the end of the text (after clearing color formatting). Default newline.

    Returns:
    None
    """
    for i in range(size - len(text)):
        text += '.'
    print(DEFAULT_COLORS.dispGREEN + text, end=DEFAULT_COLORS.RESET + end)


def center_lines(text, width):
    lines = text.split('\n')
    centered_lines = [line.center(width) for line in lines]
    return '\n'.join(centered_lines)

def get_graphics() -> dict:
    """
    Reads all graphics from the ascii directory into a dictionary.

    Parameters: None

    Returns:
    Dictionary with the key names of the graphics and the value of the graphic itself.
    The graphics are read from the ascii folder, where the key is the filename and the value is the graphic.
    """
    text_dict = {}
    for dir_name, sub_dirs, files in os.walk("./ascii/"):
        for file in files:
            with open(os.path.join(dir_name, file), encoding='utf-8') as ascii_text:
                full_file = ascii_text.read()
                split_file = full_file.splitlines(True)
                no_header_ascii = ''.join(split_file[1:])
                if (split_file[0].strip() == "GAMEBD"):
                    text_dict[file] = bytes(no_header_ascii, 'utf-8').decode('unicode_escape').encode('latin-1').decode(
                        'utf-8')
                elif (split_file[0].strip() == "CENTER"):
                    text_dict[file] = center_lines(no_header_ascii, 75)
                elif (split_file[0].strip() == "NWLCUT"):
                    text_dict[file] = no_header_ascii.replace('\n', '')
                elif (split_file[0].strip() == "NSTRIP"):
                    text_dict[file] = no_header_ascii.strip()
                elif (split_file[0].strip() == "LSTRIP"):
                    text_dict[file] = no_header_ascii.lstrip()
                elif (split_file[0].strip() == "RSTRIP"):
                    text_dict[file] = no_header_ascii.rstrip()
                else:
                    text_dict[file] = '\n' + full_file
    return text_dict

g = get_graphics()
# Use this object to access all graphics, instead of calling get_graphics() every time.
COLORS = MYCOLORS  # since MYCOLORS now lives in this file

def set_cursor(x: int, y: int) -> None:
    print(f"\033[{y};{x}H", end="")


def set_cursor_str(x: int, y: int) -> str:
    return f"\033[{y};{x}H"