from .botterino import main


def run():
    try:
        main()
    except KeyboardInterrupt:
        print("\nbye! 👋")


if __name__ == "__main__":
    run()
