from tkinter import *
from tkinter import ttk
from .config import roundfile
from .Loader.loader import append, load
from .botterino import main
from sty import fg
from threading import Thread

root = Tk()
root.title("Botterino")

# Todo: place this in a sensible place
class Stopper:
    def __init__(self):
        self.stopped = False
    def __bool__(self):
        return self.stopped
    def stop(self):
        self.stopped = True
    def unstop(self):
        self.stopped = False

class Runner:
    def __init__(self):
        self.stopper = Stopper()
        self.T = Thread(target=main, args=(self.stopper,))
    def start(self):
        self.stopper.unstop()
        self.T.start()
    def stop(self):
        self.stopper.stop()
        self.T = Thread(target=main, args=(self.stopper,))

R = Runner()

def append_entry():
    name_input = str(name.get())
    if not name_input:
        error_text.set("Name is missing")
        return
    d = load(roundfile)
    if d and name_input in d:
        error_text.set("Name is not unique")
        return
    title_input = title.get()
    if not title_input:
        error_text.set("Title is missing")
        return
    answer_input = answer.get()
    tolerance_input = ""
    if tolerance.get():
        try:
            tolerance_input = int(tolerance.get())
        except:
            error_text.set("Tolerance must be a number")
            return
    if tolerance_input and not answer_input:
        error_text.set("Answer missing when tolerance is present")
        return
    url_input = url.get()
    if not url_input:
        error_text.set("URL is missing")
        return
    manual_input = bool(manual.get())
    data = {}
    inner = {}
    if title_input:
        inner["title"] = title_input
    if answer_input:
        inner["answer"] = answer_input
    if tolerance_input:
        inner["tolerance"] = tolerance_input
    if url_input:
        inner["url"] = url_input
    if manual_input:
        inner["manual"] = manual_input
    data[name_input] = inner
    append(data, roundfile)
    clear_entries()
    print(f'{fg.green}Added round {name_input} to rounds.yaml{fg.rs}')

def clear_entries():
    name_entry.delete(0, END)
    title_entry.delete(0, END)
    answer_entry.delete(0, END)
    tolerance_entry.delete(0, END)
    url_entry.delete(0, END)
    error_text.set("")
    manual.set(False)

def start_botterino():
    #dummy function to start botterino
    R.start()

def stop_botterino():
    #dummy function to end botterino
    R.stop()

mainframe = ttk.Frame(root, padding="3 6 3 12")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

ttk.Label(mainframe, text="Name").grid(column=1, row=1, sticky=W)
ttk.Label(mainframe, text="Title").grid(column=1, row=2, sticky=W)
ttk.Label(mainframe, text="Answer").grid(column=1, row=3, sticky=W)
ttk.Label(mainframe, text="Tolerance").grid(column=1, row=4, sticky=W)
ttk.Label(mainframe, text="URL").grid(column=1, row=5, sticky=W)
ttk.Label(mainframe, text="Manual").grid(column=1, row=6, sticky=W)

error_text = StringVar()
error_label = ttk.Label(mainframe, foreground="red", textvariable=error_text)
error_label.grid(column=1, row=7, sticky=(W,E))

name = StringVar()
name_entry = ttk.Entry(mainframe, width=50, textvariable=name)
name_entry.grid(column=2, row=1, sticky=(W, E))

title = StringVar()
title_entry = ttk.Entry(mainframe, width=50, textvariable=title)
title_entry.grid(column=2, row=2, sticky=(W, E))

answer = StringVar()
answer_entry = ttk.Entry(mainframe, width=50, textvariable=answer)
answer_entry.grid(column=2, row=3, sticky=(W, E))

tolerance = StringVar()
tolerance_entry = ttk.Entry(mainframe, width=50, textvariable=tolerance)
tolerance_entry.grid(column=2, row=4, sticky=(W, E))

url = StringVar()
url_entry = ttk.Entry(mainframe, width=50, textvariable=url)
url_entry.grid(column=2, row=5, sticky=(W, E))

manual = BooleanVar(value=False)
manual_entry = ttk.Checkbutton(mainframe, variable=manual, onvalue=True, offvalue=False)
manual_entry.grid(column=2, row=6, sticky=(W, E))

ttk.Button(mainframe, text="Clear", command=clear_entries).grid(column=2, row=7, sticky=W)
ttk.Button(mainframe, text="Submit", command=append_entry).grid(column=2, row=7, sticky=E)
ttk.Button(mainframe, text="Start", command=start_botterino).grid(column=2, row=8, sticky=W)
ttk.Button(mainframe, text="Stop", command=stop_botterino).grid(column=2, row=8, sticky=E)

for child in mainframe.winfo_children():
    child.grid_configure(padx=5, pady=2)

root.mainloop()

