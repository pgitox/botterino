from posterino import load_rounds, post_round, wait
import time

while True:
    rounds = load_rounds()
    wait()
    if not rounds:
        rounds = load_rounds()
    try:
        for r in rounds:
            post_round(r)
            wait()
    except TypeError as e:
        print("No rounds in round file!", e)
        time.sleep(15)