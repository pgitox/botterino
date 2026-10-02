import os
import tkinter as tk
from threading import Thread
from tkinter import filedialog, ttk

from sty import fg

from . import botfiles
from .botterino import main as runBotterino
from .Loader.loader import append, load, roundfile
from .Utils.color import colormsg
from .validate import roundErrors


class Stopper:
    def __init__(self):
        self.stopped = False

    def __bool__(self):
        return self.stopped

    def stop(self):
        self.stopped = True


class Runner:
    def __init__(self):
        self.stopper = Stopper()
        self.thread = None

    def running(self):
        return self.thread is not None and self.thread.is_alive()

    def start(self):
        if self.running():
            if not self.stopper:
                colormsg("Botterino is already running", fg.yellow)
                return
            colormsg("Botterino is still stopping, try again in a moment", fg.yellow)
            return
        self.stopper = Stopper()
        self.thread = Thread(target=runBotterino, args=(self.stopper,), daemon=True)
        self.thread.start()

    def stop(self):
        if self.running():
            colormsg("Stopping botterino...", fg.yellow)
        self.stopper.stop()


class App:
    FIELDS = ["Name", "Title", "Answer", "Tolerance", "URL", "Image", "Message"]

    def __init__(self, root):
        self.root = root
        self.runner = Runner()
        root.title("Botterino")

        frame = ttk.Frame(root, padding="8 8 8 12")
        frame.grid(column=0, row=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        frame.columnconfigure(2, weight=1)

        self.vars = {}
        self.entries = {}
        for row, field in enumerate(self.FIELDS, start=1):
            ttk.Label(frame, text=field).grid(column=1, row=row, sticky="w")
            var = tk.StringVar()
            entry = ttk.Entry(frame, width=50, textvariable=var)
            entry.grid(column=2, row=row, sticky="we")
            self.vars[field], self.entries[field] = var, entry
        ttk.Button(frame, text="Browse…", command=self.browse).grid(
            column=3, row=self.FIELDS.index("Image") + 1, sticky="w"
        )

        row = len(self.FIELDS) + 1
        ttk.Label(frame, text="Manual").grid(column=1, row=row, sticky="w")
        self.manual = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, variable=self.manual).grid(column=2, row=row, sticky="w")

        self.error = tk.StringVar()
        ttk.Label(
            frame, foreground="red", textvariable=self.error, wraplength=420
        ).grid(column=1, row=row + 1, columnspan=3, sticky="we")

        buttons = ttk.Frame(frame)
        buttons.grid(column=2, row=row + 2, sticky="we")
        ttk.Button(buttons, text="Clear", command=self.clear).pack(side="left")
        ttk.Button(buttons, text="Add round", command=self.appendEntry).pack(
            side="right"
        )

        controls = ttk.Frame(frame)
        controls.grid(column=2, row=row + 3, sticky="we")
        ttk.Button(controls, text="Start", command=self.runner.start).pack(side="left")
        ttk.Button(controls, text="Stop", command=self.runner.stop).pack(side="right")

        for child in frame.winfo_children():
            child.grid_configure(padx=5, pady=2)

    def browse(self):
        path = filedialog.askopenfilename(
            initialdir=botfiles.imagesdir,
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif"), ("All files", "*")],
        )
        if not path:
            return
        # keep paths short when the image is in the images folder
        try:
            relative = os.path.relpath(path, botfiles.imagesdir)
            if not relative.startswith(".."):
                path = relative
        except ValueError:
            pass
        self.vars["Image"].set(path)

    def appendEntry(self):
        values = {k: v.get().strip() for k, v in self.vars.items()}
        name = values["Name"]
        if not name:
            self.error.set("Name is missing")
            return
        existing = load(roundfile)
        if existing and name in existing:
            self.error.set("Name is not unique")
            return

        r = {}
        for field, key in [
            ("Title", "title"),
            ("Answer", "answer"),
            ("URL", "url"),
            ("Image", "path"),
            ("Message", "message"),
        ]:
            if values[field]:
                r[key] = values[field]
        if values["Tolerance"]:
            try:
                r["tolerance"] = float(values["Tolerance"])
            except ValueError:
                self.error.set("Tolerance must be a number")
                return
        if self.manual.get():
            r["manual"] = True

        errors = roundErrors(r)
        if errors:
            self.error.set("\n".join(errors))
            return
        append({name: r}, roundfile)
        self.clear()
        colormsg(f"Added round {name} to rounds.yaml", fg.green)

    def clear(self):
        for var in self.vars.values():
            var.set("")
        self.error.set("")
        self.manual.set(False)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
