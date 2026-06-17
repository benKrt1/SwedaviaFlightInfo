"""Entry point for the interactive Swedavia Flight Tracker menu.

Run from the repo root:

    python3 main.py          # inside the venv
    .venv/bin/python main.py
"""

try:
    from app.menu import main
except ModuleNotFoundError:
    print("Dependencies missing. Run it with:  .venv/bin/python main.py")
    raise SystemExit(1)


if __name__ == "__main__":
    raise SystemExit(main())
