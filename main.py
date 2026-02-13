"""
This is a program for reading in datasets and compare them/print them.
It contains:
- selecting the folder to the datasets
"""
# import libs
# lib for import fold or file 
from tkinter import Tk
import tkinter.filedialog as f_diag

def pick_folder(title="choose a folder", initial_dir=None):
    """
    this is a function to open a dialog and select the folder (where the datasets need to be).
    It returns the selected path.
    
    (str) title: this is the titel of the window. If no titel was given, show default "choose a folder"
    (str) initial_dir: this is the path that opens with the window.
    """

    root = Tk()
    root.withdraw()  # don't show an empty window
    root.attributes("-topmost", True)  # bring the dialog to the front

    folder = f_diag.askdirectory(
        title=title,
        initialdir=initial_dir  # start file
    )

    root.destroy()
    return folder


# main program:
if __name__ == "__main__":

    # step 1: select the folder where the datasets lay:
    folder_path = pick_folder(
        title="Select the folder where the datasets are",
        initial_dir="C:/"
    )

