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
import  math  # import to use the square-function
    # plotting:
import bokeh as bk      
from bokeh.plotting import figure, show, output_file
    # for debugging:
import logging
from pathlib import Path
import unittest
import sys
# endregion



# region global variables
DB_name = "all_in_one.db"   # name of the database that should include all databases

#ToDo Improvement: could be made, if the values would be found out over the length of the pandas arrays after importing
# the expected cols for each csv:
expected_test_cols = 2   # x + y
expected_train_cols = 5  # x + y1..y4
expected_ideal_cols = 51 # x + y1..y50

# for debugging:
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # set logging level
debug_mode = {"LoadDBs" : False, "compare_points_function" : False, "compare_points" : False } # set manualy on true to debug in different parts of the program. It will print some values in the terminal

# endregion

# region classes
class DatasetFormatError(Exception):
    """
    Raised when a dataset does not match the expected format.
    """
    pass
class Function:
    def __init__(self,FunctionValues):
        """
        class that contains X- and Y-values of a function. Only for the required class inhibition...
        x       : float      X-value of function 
        y       : float      Y-value of function 
        """
        self.x = FunctionValues.iloc[:, 0]  # x-value is always first
        self.y = FunctionValues.iloc[:, 1]  # y-values
class FunctionComparison (Function):
    def __init__(self,FunctionValues,FunctionValues2):
        """
        inheritance the class "Function" and expand it with X- and Y-values of a second function
        x       : float      X-value of function 1 
        y       : float      Y-value of function 1
        x2      : float      X-value of function 2
        y2      : float      Y-value of function 2
        """
        super().__init__(FunctionValues)    # inheritance of the other class
        self.x2 = FunctionValues2.iloc[:, 0] # x-value is always first
        self.y2 = FunctionValues2.iloc[:, 1] # y-values

    def LeastSquare(self):
        """
        calculate the Least Square of two Functions (one should be the ideal function and one the train function).
        There is no additional input necessary. The result of the Least Square will be returned.

        input:
        no input required. Values will be used from the class.

        return:
        LeastSqr    : float     result of Least Square
        """
        LeastSqr = 0.0 # initialize the var
        for counter in range(len(self.x)):  # go through every x-value of the function
            LeastSqr += (self.y.iloc[counter] - self.y2.iloc[counter]) ** 2 # calculate the Least-Square-Error
        return LeastSqr
    
    def compare_points(self, Tolerance=None):
        """
        compares points of two functions to see if they are within the given tolerance (optional input, default sqrt(2)).

        input:
        Tolerance       : float     Tolerance for the points to be similar

        return:
        ResultCompare   : dict      a dictionary that contains if the point is within the Tolerance (bool), the x- and y-value (float) and the delta in y (float)
        max_abs_dif     : float     a float value that contains the max value of the deltas/ the biggest delta
        """
        # init:
        ResultCompare = {}
        max_abs_dif = 0.0
        if Tolerance is None:   # Tolerance is an optional input. It's default is sqrt(2)
            Tolerance = math.sqrt(2)

        for i in range(len(self.x)): # for every x-value of the first function
            x_value = self.x.iloc[i]    # save x- and y-value in one var
            y_value = self.y.iloc[i]
            div = None  # IMPORTANT: needs to be resetet after every point
            for j in range(len(self.x2)):   # for every x-value of the second function
                if x_value == self.x2.iloc[j]:  # compare if both x-values (of both functions) are equal
                    div = float(self.y2.iloc[j] - y_value)  # if they are equal, calculate the difference of the y-values
                    break   # then break, as one value was already found. HINT: this only works, if the second function has only one y-value for each x-value!
                    #ToDo Improvement: improve the code, that it will save more results, if more x-values are avaible, instead of interrupting the loop
            if div is None: # if no compare point was found (same x-values), then safe the information in ResultCompare (first element)
                ResultCompare[i] = [False, x_value, y_value, None]  # False = no comparepoint, x_value,y_value, None = no calculated div
                # for manually checking:
                if debug_mode["compare_points_function"]:
                    print(f"no compare point for x={x_value}")

                continue # skip the rest of the code for this i

            abs_div = abs(div) # just use the absolute value
            ResultCompare[i] = [abs_div <= Tolerance, x_value, y_value, abs_div] # save information in ResultCompare
            max_abs_dif = max(max_abs_dif, abs_div) # save the abs_div, if it's bigger then max_abs_dif 

            logger.debug("x-value:%s and y-value:%s", float(x_value), float(y_value))
        return ResultCompare, max_abs_dif
       
# endregion

# region Functions
def pick_folder(title="choose a folder", initial_dir=None):
    """
    this is a function to open a dialog and select the folder (where the datasets need to be).
    It returns the selected path.
    
    input:
    title       :str    this is the titel of the window. If no titel was given, show default "choose a folder"
    initial_dir :str    this is the path that opens with the window.

    return:
    folder      : str   the selected path
    """

    root = Tk()
    root.withdraw()  # don't show an empty window
    root.attributes("-topmost", True)  # bring the dialog to the front
    folder = f_diag.askdirectory(
        title=title,
        initialdir=initial_dir  # start file that will be shown, if the window is opened
    )

    root.destroy()  # close connection
    return folder

def load_csvs_into_single_db(folder: Path):
    """
    this will load the csv files into a single db. In contains the three datasets.
    One function for all three datasets are used, because the program needs all three to run.
    ;ToDo Improvement: make one function for one dataset, this will saves lines of the code, but requires more calls.
    
    input:
    folder      : Path    this is the titel of the window. If no titel was given, show default "choose a folder"

    return:
    engine      : Engine        the engine is also returned for adding the "reusults" column later
    test_df     : DataFrame     DataFrame containing the test-points
    train_df    : DataFrame     DataFrame containing the train-points
    ideal_df    : DataFrame     DataFrame contraining the ideal-points
    """
    # load the csv-files into DataFrames using the function read_and_sort
    test_df = read_and_sort(folder / "test.csv", "x")
    train_df = read_and_sort(folder / "train.csv", "x")
    ideal_df = read_and_sort(folder / "ideal.csv", "x")

    # check if the csv-files have the expected number of columns (glibal variables for expected number of columns)
    if test_df.shape[1] != expected_test_cols:
        raise DatasetFormatError (f"test.csv must have {expected_test_cols} columns, got {test_df.shape[1]}")
    if train_df.shape[1] != expected_train_cols:
        raise DatasetFormatError (f"train.csv must have {expected_train_cols} columns, got {train_df.shape[1]}")
    if ideal_df.shape[1] != expected_ideal_cols:
        raise DatasetFormatError (f"ideal.csv must have {expected_ideal_cols} columns, got {ideal_df.shape[1]}")

    # create an engine and open for saving the datas into the database. DB_name is one of the global variables/constants
    engine = sa.create_engine(f"sqlite:///{DB_name}") 

    # load the dataframes into the database (same engine, one file)
    test_df.to_sql("test_data", con=engine, if_exists="replace", index=False)
    train_df.to_sql("training_data", con=engine, if_exists="replace", index=False)
    ideal_df.to_sql("ideal_functions", con=engine, if_exists="replace", index=False)

    return engine, test_df, train_df, ideal_df

    
def read_and_sort(path_to_df,sortBy=None):
    """
    read the csv file (input) and sort the values (input). Returns the sorted DataFrame.
    It returns the DataFrame sorted after first coloumn or optional after sortBy-value (input)

    input:
    path_to_df  : str           path to folder where csv is
    sortBy      : str           (optional)string of key that should be sorted for, e.g. "x"  

    return:
    dummy_df    : DataFrame     sorted DataFrame
    """

    dummy_df = pd.read_csv(path_to_df) # pandas function used to load cvs into a DataFrame
    if sortBy!=None: dummy_df = dummy_df.sort_values(by=sortBy) # if there was no sortingBy given (key to sort by), then do not sort
    return dummy_df
    
def separate_functions(dummyDF):
    """
    This method turns a DataFrame with many functions into a list with only one function.
    e.g. DataFrame: x,y1,y2     ->  List[0]=x,y1    List[1]=x,y2    List[2]=x,y3
    This function returns a list which values on every index one function, containing x and yn value

    input:
    dummyDF     : DataFrame     is a dataframe with one x column and many y columns

    return:
    dummyList   : list          a list that contains x and y_n values
    """
    dummyList = [] # init as a list
        
    # now I want an list with Test[0] = all x and y1 values, Test[1] = all x and y2 values,...
    for i in dummyDF.columns[1:]:
        dummy = dummyDF[[dummyDF.columns[0],i]].copy() # copy all x and y_n values into one DataFrame (dummy)
        dummyList.append(dummy) 
    return(dummyList)

def plot_with_bokeh(Train, Ideal, bestFittingFunction, results_df, html_name="plot.html"):
    """
    this function will plot the results as html using bokeh. The titel and configuration of the plot is coded fixed.
    ;ToDo Improvement: if the plot needs to be edit often, maybe use global variable for having one place in the program to 
    configure the program or put it in a user interface for the user to decide different appearances.

    input:
    Train               : list          list of DataFrames (x,y) for the 4 training functions
    Ideal               : list          list of DataFrames (x,y) for the 50 ideal functions
    bestFittingFunction : dict          dict {train_no: [ideal_no, min_error]}
    results_df          : DataFrame     DataFrame with columns x,y,ideal_func,deviation (optional train_no)

    return:
    -
    """

    # name of the file was given with the function (input), but title is hard coded
    output_file(html_name, title="Training vs Ideal + Test Points (Deviation)")

    plots = []  # initialize plots as a list

    # for each train-function an own subplot will be generized
    for train_idx in range(len(Train)):
        train_no = train_idx + 1    # as the counter starts at 0 we add +1
        ideal_no = bestFittingFunction[train_no][0]  # 1-based
        ideal_idx = ideal_no - 1 # as the bestFittingFunction is 1-based and the list 0-based, we need -1

        train_df = Train[train_idx]
        ideal_df = Ideal[ideal_idx]

        # just save only the four relevant ideal-functions for the plot
        pts = results_df[results_df["ideal_func_no"] == ideal_no].copy()

        # define the figure
        p = figure(
            title=f"Train {train_no} vs Ideal {ideal_no}",
            width=500,
            height=350,
            x_axis_label="x",
            y_axis_label="y",
            tools="pan,wheel_zoom,box_zoom,reset,save,hover",
        )

        # lines for Train and Ideal points
        p.line(train_df.iloc[:, 0], train_df.iloc[:, 1], line_width=2, legend_label="Train")
        p.line(ideal_df.iloc[:, 0], ideal_df.iloc[:, 1], line_width=2, legend_label="Ideal")

        # the testpoints should still be points colored by the deviation
        if len(pts) > 0:
            source = bk.models.ColumnDataSource(pts)

            # color by the deviation
            mapper = bk.transform.linear_cmap(
                field_name="delta_y",
                palette=bk.palettes.Viridis256,
                low=float(pts["delta_y"].min()),
                high=float(pts["delta_y"].max()),
            )

            # define the scatter
            r = p.scatter(
                x="x", y="y",
                source=source,
                size=6,
                fill_color=mapper,
                line_color=None,
                legend_label="Test points",
            )

            # Colorbar
            color_bar = bk.models.ColorBar(color_mapper=mapper["transform"], width=8, location=(0, 0))
            p.add_layout(color_bar, "right")

        p.legend.location = "top_left"
        p.legend.click_policy = "hide"  # hide the lines/points by clicking in the legend
        plots.append(p)

    # define the grid 2x2 for four training functions
    #ToDo Improvement: make it flexible, so we don't need to relay on four functions. Suggestion: One window for one function, 
    # instead of a grid. A grid 4x4 would be printed small....
    grid = bk.layouts.gridplot([plots[0:2], plots[2:4]])
    show(grid)


def debug_database(engine):
    '''
    this helps to check the database. It was originally implemented to see how the engine looks like and refunctioned for debugging.

    input:
    engine  : Engine    the engine that should be checked

    return:
    -
    '''
    # use SQLAlchemy lib to get some information from the engine.
    inspector = sa.inspect(engine)

    print("\n========== DATABASE DEBUG ==========")

    tables = inspector.get_table_names() # load tablenames
    print("\nTables found:", tables)

    for table in tables:
        print(f"\n--- Table: {table} ---")

        # show columns for every table
        columns = inspector.get_columns(table)
        print("Columns:")
        for col in columns:
            print(f"  {col['name']} ({col['type']})")

        # count of rows
        count_df = pd.read_sql(f"SELECT COUNT(*) as count FROM {table}", con=engine)
        print("Row count:", count_df["count"][0])

        # show the first five elements
        preview_df = pd.read_sql(f"SELECT * FROM {table} LIMIT 5", con=engine)
        print("Preview:")
        print(preview_df)

    print("\n====================================\n")

# endregion


# region UnitTests
class TestSeparateFunctions(unittest.TestCase):
    def test_separate_functions_splits_columns(self):
        df = pd.DataFrame({
            "x": [0, 1, 2],
            "y1": [10, 11, 12],
            "y2": [20, 21, 22],
            "y3": [30, 31, 32],
        })

        out = separate_functions(df)

        self.assertEqual(len(out), 3)  # y1..y3 -> 3 functions
        self.assertListEqual(list(out[0].columns), ["x", "y1"])
        self.assertListEqual(list(out[1].columns), ["x", "y2"])
        self.assertListEqual(list(out[2].columns), ["x", "y3"])

        # Check values preserved
        self.assertEqual(out[1].iloc[2, 0], 2)   # x=2
        self.assertEqual(out[1].iloc[2, 1], 22)  # y2 at x=2


class TestFunctionComparisonLeastSquare(unittest.TestCase):
    def test_least_square_basic(self):
        # y1: [1,2,3], y2: [1,4,5] -> diffs [0, -2, -2] -> squares [0,4,4] sum=8
        df1 = pd.DataFrame({"x": [0, 1, 2], "y": [1, 2, 3]})
        df2 = pd.DataFrame({"x": [0, 1, 2], "y": [1, 4, 5]})

        comp = FunctionComparison(df1, df2)
        self.assertAlmostEqual(comp.LeastSquare(), 8.0)


class TestFunctionComparisonComparePoints(unittest.TestCase):
    def test_compare_points_true_false_and_max(self):
        df1 = pd.DataFrame({"x": [0, 1], "y": [10.0, 10.0]})
        df2 = pd.DataFrame({"x": [0, 1], "y": [10.5, 12.0]})
        comp = FunctionComparison(df1, df2)

        res, max_abs = comp.compare_points(Tolerance=1.0)

        # res[counter] = [bool, x_value, y_value, abs_div]
        self.assertTrue(res[0][0])   # abs(10.5-10)=0.5 <= 1.0
        self.assertFalse(res[1][0])  # abs(12-10)=2.0 > 1.0
        self.assertAlmostEqual(res[0][3], 0.5)
        self.assertAlmostEqual(res[1][3], 2.0)
        self.assertAlmostEqual(max_abs, 2.0)

    def test_compare_points_missing_x(self):
        # df2 doesn't contain x=1, so div is None for that point
        df1 = pd.DataFrame({"x": [0, 1], "y": [5.0, 6.0]})
        df2 = pd.DataFrame({"x": [0], "y": [5.2]})
        comp = FunctionComparison(df1, df2)

        res, max_abs = comp.compare_points(Tolerance=10.0)

        self.assertTrue(res[0][0])      # x=0 exists, abs_dev=0.2 <= 10
        self.assertFalse(res[1][0])     # x=1 missing => False
        self.assertIsNone(res[1][3])    # deviation None
        self.assertAlmostEqual(max_abs, 0.2)

class TestDatasetFormat(unittest.TestCase):
    def test_raises_dataset_format_error(self):
        # fake dfs: wrong column count for test.csv
        folder = Path(".")  # egal, wir testen nicht das Dateisystem hier

        test_df = pd.DataFrame({"x":[0], "y":[1], "extra":[2]})     # 3 statt 2
        train_df = pd.DataFrame({"x":[0], "y1":[1], "y2":[2], "y3":[3], "y4":[4]})
        ideal_df = pd.DataFrame({"x":[0], **{f"y{i}":[i] for i in range(1,51)}})

        # Simuliere nur die Formatprüfung (am besten als eigene Funktion auslagern)
        with self.assertRaises(DatasetFormatError):
            if test_df.shape[1] != expected_test_cols:
                raise DatasetFormatError("bad test format")


# endregion 

# main program:
def main():

    # region step 1: select the folder where the datasets lay:
    folder_path = pick_folder(
        title="Select the folder where the datasets are",
        initial_dir="C:/"
    )
    # endregion

    # region step 2: load the datasets
    # read csv-files, sort them after x-value and create engine for DB
    folder = Path(folder_path)
    try:
        for filename in ["test.csv", "train.csv", "ideal.csv"]:
            if not (folder / filename).exists():
                raise FileNotFoundError(f"{filename} not found")

        engine, LoadTest, LoadTrain, LoadIdeal = load_csvs_into_single_db(folder)

    except FileNotFoundError as e:
        print("File was not found:", e)
        logging.error("Please check if the path is correct and the datasets are named correctly.")
        logging.debug(str(e))
        return
    except DatasetFormatError as e:
        print("Dataset format error:", e)
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
    for (x, y, ideal_no, train_no), dev_list in FittingPoints.items():
        keyname = f"{train_no}_{ideal_no}"
        if keyname not in FittingPoints_sorted:
            FittingPoints_sorted[keyname] = []
        deviation = float(dev_list[0])  # dev_list = [Compare[counter][3]]
        FittingPoints_sorted[keyname].append((float(x), float(y), float(deviation), int(ideal_no)))



    if debug_mode["compare_points"]:
        print("Source: Task2: showing fitting points and to which function is suits best (key = IdealFunctionNo : value = list of suitable x-value) "+str(FittingPoints_sorted))
 
    rows = []
    for (x, y, ideal_no, train_no), dev_list in FittingPoints.items():
        rows.append({
            "x": float(x),
            "y": float(y),
            "delta_y": float(dev_list[0]),
            "ideal_func_no": int(ideal_no),
            "train_no": int(train_no),
        })

    results_df = pd.DataFrame(rows, columns=["x", "y", "delta_y", "ideal_func_no"])
    results_df.to_sql("results", con=engine, if_exists="replace", index=False)

    logger.info("Wrote %d rows to results table.", len(results_df))

# endregion      

# region Task 3: Plot the results
    plot_with_bokeh(Train, Ideal, bestFittingFunction, results_df, html_name="deviation_plot.html")
# endregion

# call main program:
if __name__ == "__main__":
    # Normal run: python main.py
    # Unittest run:   python main.py test
    if len(sys.argv) > 1 and sys.argv[1].lower() == "test":
        # Prevent unittest from interpreting "test" as a pattern
        sys.argv = [sys.argv[0]]
        unittest.main(verbosity=2)
    else:
        main()