# COIN FLIP
import random
from time import sleep
from utils.screenspace import Terminal, g, overwrite

game_title = "⛁ Coin Flip"
header = "─" * ((75 - len(game_title)) // 2) + game_title + "─" * ((75 - len(game_title)) // 2)

def play(active_terminal: Terminal, bet: int):
    """
    Coin Flip

    Initializes a simple coin flip for casino.py
    A very simple base for a new casino_game
    Returns the wager to be sent to the player
    """
    score = [0,0,0,0]

    active_terminal.update(header + "\n" + g['coin_flip_heads'])
    
    choice = input(f"\rHeads or Tails? (h/T) ")
    overwrite("\r" + " " * 40)
    flip = random.choice(['heads', 'tails'])
    
    #TODO - Make the animation asynchrnous.
    active_terminal.update(header + "\n" + g['coin_flip_heads'])
    sleep(0.2)
    active_terminal.update(header + "\n" + g['coin_flip_middle'])
    sleep(0.2)
    active_terminal.update(header + "\n" + g['coin_flip_tails'])
    sleep(0.2)
    active_terminal.update(header + "\n" + g['coin_flip_middle'])
    sleep(0.2)
    active_terminal.update(header + "\n" + g['coin_flip_heads' if flip == 'heads' else 'coin_flip_tails'])

    if(choice.lower() == "h" and flip == 'heads'):
        input(f"\rYou got heads!")
        overwrite("\r" + " " * 40)
        score[0] += 1
    elif(choice.lower() == "h" and flip == 'tails'):
        input(f"\rYou got tails...")
        overwrite("\r" + " " * 40)
    elif(flip == 'heads'):
        input(f"\rYou got heads...")
        overwrite("\r" + " " * 40)
    else:
        input(f"\rYou got tails!")
        overwrite("\r" + " " * 40)
        score[0] += 1

    if(score[0] == 1):
        active_terminal.update(header + "\n" + g['casino_win'])
        bet *= 2
    else:
        active_terminal.update(header + "\n" + g['casino_lose'])
        bet = 0
    input("\r")
    overwrite("\r" + " " * 40)
    return bet
