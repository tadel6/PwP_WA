"""
This is a program for reading in datasets and compare them/print them.
It contains:
- selecting the folder to the datasets
"""
# region import libs
    # import fold or file:
from tkinter import Tk
import tkinter.filedialog as f_diag
    # tools for datasets:
import pandas as pd
import sqlalchemy as sa
import sqlite3
    # for logging:
import logging
from pathlib import Path
import unittest
    # for operations in the functions:
import matplotlib.pyplot as plt # for visualizing the functions
import  math  # import to use the square-function
# endregion



# region global variables
logger = logging.getLogger(__name__)
debug_mode = {"LoadDBs" : True, "compare_points_function" : False, "compare_points" : False } # set manualy on true to debug in different parts of the program. Just for me...
logging.basicConfig(level=logging.INFO) # set logging level

DB_name = "project.db"

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

def load_csvs_into_single_db(folder: Path):
    # 1) CSVs laden
    test_df = read_and_sort(folder / "test.csv", "x")
    train_df = read_and_sort(folder / "train.csv", "x")
    ideal_df = read_and_sort(folder / "ideal.csv", "x")

    # 2) Spalten prüfen (user-defined exception kommt später als eigener Schritt)
    expected_test_cols = 2
    expected_train_cols = 9  # x + y1..y4
    expected_ideal_cols = 51 # x + y1..y50
    if test_df.shape[1] != expected_test_cols:
        raise ValueError(f"test.csv must have {expected_test_cols} columns, got {test_df.shape[1]}")
    if train_df.shape[1] != expected_train_cols:
        raise ValueError(f"train.csv must have {expected_train_cols} columns, got {train_df.shape[1]}")
    if ideal_df.shape[1] != expected_ideal_cols:
        raise ValueError(f"ideal.csv must have {expected_ideal_cols} columns, got {ideal_df.shape[1]}")

    # 3) Eine DB, zwei Tabellen
    engine = sa.create_engine(f"sqlite:///{DB_name}")

    test_df.to_sql("test_data", con=engine, if_exists="replace", index=False)
    train_df.to_sql("training_data", con=engine, if_exists="replace", index=False)
    ideal_df.to_sql("ideal_functions", con=engine, if_exists="replace", index=False)

    return engine, test_df, train_df, ideal_df

    
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
    
def separate_functions(dummyDF):
    """
    This method turns a DataFrame with many functions into a list with only one function.
    e.g. DataFrame: x,y1,y2     ->  List[0]=x,y1    List[1]=x,y2    List[2]=x,y3
    This function returns a list which values on every index one function, containing x and yn value

    input:
    dummyDF : DataFrame     ; is a dataframe with one x column and many y columns
    """
    dummyList = []
        
    # now I want an list with Test[0] = all x and y1 values, Test[1] = all x and y2 values,...
    for i in dummyDF.columns[1:]:
        dummy = dummyDF[[dummyDF.columns[0],i]].copy() # copy all x and y_n values into one DataFrame (dummy)
        dummyList.append(dummy) 
    return(dummyList)

def debug_database(engine):
    inspector = sa.inspect(engine)

    print("\n========== DATABASE DEBUG ==========")

    tables = inspector.get_table_names()
    print("\nTables found:", tables)

    for table in tables:
        print(f"\n--- Table: {table} ---")

        # Spalten anzeigen
        columns = inspector.get_columns(table)
        print("Columns:")
        for col in columns:
            print(f"  {col['name']} ({col['type']})")

        # Anzahl Zeilen
        count_df = pd.read_sql(f"SELECT COUNT(*) as count FROM {table}", con=engine)
        print("Row count:", count_df["count"][0])

        # Erste 5 Zeilen anzeigen
        preview_df = pd.read_sql(f"SELECT * FROM {table} LIMIT 5", con=engine)
        print("Preview:")
        print(preview_df)

    print("\n====================================\n")

# endregion

# region classes
class FunctionComparison ():
    def __init__(self,FunctionValues1,FunctionValues2):# XvalueFunct1, YvalueFunct1,XvalueFunct2, YvalueFunct2):
        """
        inheritance the class "Function" and expand it with X- and Y-values of a second function
        X   : float ; X-value of function 1
        Y   : float ; Y-value of function 1
        X2   : float ; X-value of function 2
        Y2   : float ; Y-value of function 2
        """
        
                # Get list of column names (in order)
        cols1 = FunctionValues1.columns.tolist() 
        cols2 = FunctionValues2.columns.tolist() 
        self.X1 = FunctionValues1[cols1[0]]
        self.Y1 = FunctionValues1[cols1[1:]] 
        self.X2 = FunctionValues2[cols2[0]]
        self.Y2 = FunctionValues2[cols2[1:]] 
    
    def LeastSquare(self):
        """
        calculate the Least Square of two Functions (one should be the ideal function and one the "measured"/train function).
        There is no additional input necessary. The result of the Least Square will be returned.

        input:
        -

        return:
        LeastSqr    : float     ; result of Least Square
        """
        LeastSqr = 0.0
        #for counter in range(1,len(self.X1)):
        for counter in range(len(self.X1)):

            LeastSqr += (self.Y1.iloc[counter,0] - self.Y2.iloc[counter,0]) ** 2  
        return LeastSqr
    
    def compare_points(self, Tolerance=math.sqrt(2)):
        """
        compares points of two functions to see if they are within the given tolerance (optional input, default sqrt(2)).
        returns: dict with x-value as key and the result as value (bool) 

        input:
        Tolerance   : float     ; Tolerance for the points to be similar
        """
        ResultCompare = {}
        max_abs_dif = 0.0

        for counter in range(len(self.X1)):
            x_value = self.X1.iloc[counter]
            y_value = self.Y1.iloc[counter, 0]

            div = None  # WICHTIG: pro Punkt resetten

            for counter2 in range(len(self.X2)):
                if x_value == self.X2.iloc[counter2]:
                    div = float(self.Y2.iloc[counter2, 0] - y_value)
                    break

            if div is None:
                ResultCompare[counter] = [False, x_value, y_value, None]
                if debug_mode["compare_points_function"]:
                    print(f"no compare point for x={x_value}")
                continue

            abs_div = abs(div)
            ResultCompare[counter] = [abs_div <= Tolerance, x_value, y_value, abs_div]
            max_abs_dif = max(max_abs_dif, abs_div)

            logger.debug("x-value:%s and y-value:%s", float(x_value), float(y_value))
        return ResultCompare, max_abs_dif


       
# endregion

# main program:
def main():

    # region step 1: select the folder where the datasets lay:
    folder_path = pick_folder(
        title="Select the folder where the datasets are",
        initial_dir="C:/"
    )
    # ednregion

    # region step 2: load the datasets
    # read csv-files, sort them after x-value and create engine for DB
    folder = Path(folder_path)
    try:
        for filename in ["test.csv", "train.csv", "ideal.csv"]:
            if not (folder / filename).exists():
                raise FileNotFoundError(f"{filename} not found")

        engine, LoadTest, LoadTrain, LoadIdeal = load_csvs_into_single_db(folder)

    except FileNotFoundError as e:
        logging.error("Please check if the path is correct and the datasets are named correctly.")
        logging.debug(str(e))
        return
    except ValueError as e:
        logging.error("Dataset format error.")
        logging.debug(str(e))
        return

    # test if everything was loaded correct
    if debug_mode["LoadDBs"]:
        debug_database(engine)

    # initialize empty lists to store the values of each csv
    Test = []
    Train = []
    Ideal = []
    
    # now I want an list with Test[0] = all x and y1 values, Test[1] = all x and y2 values,...
    Test = separate_functions(LoadTest)
    Train = separate_functions(LoadTrain)
    Ideal = separate_functions(LoadIdeal)

# region Task 1: Find the best fitting ideal function for the training functions with LeastSquare
    bestFittingFunction = {}
    # for each function in Train:
    for CounterTrain in range(len(LoadTrain.columns[1:])):
        # initialize the comparison value to the first given result, so we can use it to compare it later with the following LeastSquareErrors
        minError = FunctionComparison.LeastSquare(FunctionComparison(Train[CounterTrain],Ideal[0]))
        FittingIdealFunction = 0 # because it starts with index 0, so the ideal function is index + 1, in this case we set as init value ideal function = 1
        # for each function in ideal:
        for CounterIdeal in range(len(LoadIdeal.columns[1:])):
            # calculate the LeastSquare Error
            LeastE = FunctionComparison.LeastSquare(FunctionComparison(Train[CounterTrain],Ideal[CounterIdeal]))
            # if you found a smaller error, then save the value and ideal function No.:
            if LeastE <= minError:
                minError = LeastE # to refresh the minError to the smallest known value
                FittingIdealFunction = CounterIdeal # save the fitting function No.
            #print(CounterIdeal)
        # this dict saves the train function and his best fitting ideal function. key = train function number, value = ideal function number
        bestFittingFunction[CounterTrain+1] = [FittingIdealFunction+1,minError] # because the index starts at 0, but our first function starts with y1, the actual function ist Index+1
        # print the result which functions fit best
        print(f"LeastSquare: the best fitting function for training data {CounterTrain+1} is ideal function = "+ str(bestFittingFunction[CounterTrain+1][0])+" with a Least Square Error of ~"+str(minError))


# region Task 2: Compare every point in test with the four fitting ideal function from Task 1
    if debug_mode["compare_points"]:
        print("Source Task2: Counted columns in Test.csv = "+str(len(Test[0])))
        print("Source Task2: Counted best fitting founded Functions from Ideal: "+str(len(bestFittingFunction)))
        print("Source Task2: best fitting function no. and LSE: "+str(bestFittingFunction))

    # for each fitting function in ideal:
    FittingPoints = {}
    FoundFittingIdealFunctions = []
    for CounterIdeal in range(1,len(bestFittingFunction)+1):
        # first Compare the points (Train-Function to his best fitting Ideal function) to get the max difference between two points. (default tolerance is sqrt(2))
        Compare,maxDifference = FunctionComparison.compare_points(FunctionComparison(Train[CounterIdeal-1],Ideal[bestFittingFunction[CounterIdeal][0]-1]))
        if debug_mode["compare_points"]:
            print("source: Task2: Compare Functions: Function:" + str(Train[CounterIdeal-1])+"with Ideal: "+str(Ideal[bestFittingFunction[CounterIdeal][0]-1]) + "and max dif: "+str(maxDifference))
        # then set the max Difference multiplied with sqrt(2) as Tolerance for the comparision with the Test-Dataset
        Tolerance = maxDifference*math.sqrt(2)
        Compare,dummy = FunctionComparison.compare_points(FunctionComparison(Test[0],Ideal[bestFittingFunction[CounterIdeal][0]-1]),Tolerance)
        for counter in range(1,len(Compare)):
            if Compare[counter][0]: # if comparision gave out a True for the point "counter" (True means the compared point is within the given Tolerance)
                FittingPoints[Compare[counter][1],Compare[counter][2],bestFittingFunction[CounterIdeal][0],CounterIdeal] =[Compare[counter][3]] # set the analyzed ideal function to the dict
        FoundFittingIdealFunctions.append(bestFittingFunction[CounterIdeal][0])

    # save all fitting points for each (of the four) ideal found function into a dict. With key as the No. of ideal Function and  value as the x-value of the similar point from Test-dataset
    FittingPoints_sorted = {}
    for x, y, z, a in list(FittingPoints.keys()):
        keyname = str(a)+"_"+str(z)
        if keyname not in FittingPoints_sorted:
            FittingPoints_sorted[keyname] = []  # new List for another ideal function No.
        FittingPoints_sorted[keyname].append((float(x),float(y)))

    if debug_mode["compare_points"]:
        print("Source: Task2: showing fitting points and to which function is suits best (key = IdealFunctionNo : value = list of suitable x-value) "+str(FittingPoints_sorted))

# endregion       

# region Task 3: Plot the results
    rows = 2
    cols = 4
    fig, axes = plt.subplots(rows, cols, figsize=(10,8))
    axes = axes.flatten()

    for eachTrain in range(len(Train)):
        x_Train = Train[eachTrain].iloc[:,0]  # erste Spalte: x
        y_Train = Train[eachTrain].iloc[:,1]
        x_Ideal = Ideal[bestFittingFunction[eachTrain+1][0]-1].iloc[:,0]
        y_Ideal = Ideal[bestFittingFunction[eachTrain+1][0]-1].iloc[:,1]
        key = f"{eachTrain+1}_{bestFittingFunction[eachTrain+1][0]}"
        points = FittingPoints_sorted.get(key, [])
        x_values = [p[0] for p in points]
        y_values = [p[1] for p in points]
        ax = axes[eachTrain]
        ax.plot(x_Train, y_Train, color='blue', label="Train")
        ax.plot(x_Ideal, y_Ideal, color='red', label="Ideal")
        ax.scatter(x_values, y_values, color='green', label="Test points")
        ax.set_title('Train function No: '+str(eachTrain+1)+ " with Ideal function No: "+str(bestFittingFunction[eachTrain+1][0]))
        ax.legend()

    plt.show()


# endregion

# call main program:
if __name__ == "__main__":
    main()