"""
This is a program for reading in datasets and compare them/print them.
It contains:
- selecting the folder to the datasets
"""
# import libs
# lib for import fold or file 
from tkinter import Tk
import tkinter.filedialog as f_diag
# tools for datasets
import pandas as pd
from sqlalchemy import create_engine
import sqlite3
#  for logging:
import logging
from pathlib import Path




# region global variables

debugingmode = {"LoadDBs" : True } # set manualy on true to debug in different parts of the program. Just for me...
logging.basicConfig(level=logging.DEBUG) # set logging level

# endregion

# region Functions
def pick_folder(title="choose a folder", initial_dir=None):
    """
    this is a function to open a dialog and select the folder (where the datasets need to be).
    It returns the selected path.
    
    title       :str    this is the titel of the window. If no titel was given, show default "choose a folder"
    initial_dir :str    this is the path that opens with the window.
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
# endregion

# region classes
class Function():
    def __init__(self,FunctionValues):
        """
        class that contains X- and Y-values of a function
        """
        # Get list of column names (in order)
        cols = FunctionValues.columns.tolist()

        self.X = FunctionValues[cols[0]] 
        self.Y = FunctionValues[cols[1:]] 

    def read_and_sort(path_to_df,sortBy=None):
        """
        read the csv file (input) and sort the values (input). Returns the sorted DataFrame.
        It returns the DataFrame sorted after first coloumn or optional after sortBy-value (input)

        path_to_df  :str    path to folder where csv is
        sortBy      :str   (optional)string of key that should be sorted for, e.g. "x"  
        """

        dummy_df = pd.read_csv(path_to_df)
        if sortBy!=None: dummy_df = dummy_df.sort_values(by=sortBy)
        return dummy_df
# endregion

# main program:
if __name__ == "__main__":

    # step 1: select the folder where the datasets lay:
    folder_path = pick_folder(
        title="Select the folder where the datasets are",
        initial_dir="C:/"
    )

    # step 2: load the datasets
    # read csv-files, sort them after x-value and create engine for DB
    folder = Path(folder_path)
    try:
        for filename in ["test.csv", "train.csv", "ideal.csv"]:
            if not (folder / filename).exists():
                raise FileNotFoundError(f"{filename} not found")

        LoadTest = Function.read_and_sort(folder / "test.csv", "x")
        TestEngine = create_engine('sqlite:///test.db')

        LoadTrain = Function.read_and_sort(folder / "train.csv", "x")
        TrainEngine = create_engine('sqlite:///train.db')

        LoadIdeal = Function.read_and_sort(folder / "ideal.csv", "x")
        IdealEngine = create_engine('sqlite:///ideal.db')

        LoadTest.to_sql('test_data', con=TestEngine, if_exists='replace', index=False)
        LoadTrain.to_sql('training_data', con=TrainEngine, if_exists='replace', index=False)
        LoadIdeal.to_sql('ideal_data', con=IdealEngine, if_exists='replace', index=False)

    except FileNotFoundError as e:
        logging.error("Please check if the path is correct and the datasets are named correctly.")
        logging.debug(str(e))



# region UnitTest: read DB
    if debugingmode['LoadDBs']:
        # UnitTest: read from DB and print
        print("Debuging: Read SQL DB")
        debug_sql = pd.read_sql('SELECT * FROM test_data', con=TestEngine)
        print("test DB: \n"+str(debug_sql.head()))
        debug_sql = pd.read_sql('SELECT * FROM training_data', con=TrainEngine)
        print("train DB: \n"+str(debug_sql.head()))
        debug_sql = pd.read_sql('SELECT * FROM ideal_data', con=IdealEngine)
        print("ideal DB: \n"+str(debug_sql.head()))
        conn = sqlite3.connect("ideal.db")
        
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        print("Tabellen:", cursor.fetchall())
        conn.close()
# endregion