from botterino.posterino import post_round, wait
from Loader.loader import load_rounds
import time

while True:
    rounds = load_rounds()
    try:
        for r in rounds:
            wait()
            post_round(r)
    except RuntimeError as e:
        print("No rounds in round file!")
        time.sleep(5)
        continue