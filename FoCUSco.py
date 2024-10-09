from pathlib import Path
import pandas as pd
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
import shutil
import sys
import matplotlib.pyplot as plt
import seaborn as sns

def selectDirectory():
    """
    Prompts the user to select a directory using a file dialog.
    This function opens a file dialog window that allows the user to select a directory.
    If a directory is selected, it prints the selected directory path and returns it as a Path object.
    If no directory is selected, it prints a message and terminates the program.
    Returns:
        Path: The path of the selected directory if a directory is selected.
    Raises:
        SystemExit: If no directory is selected, the program will terminate.
    """

    selected_directory = filedialog.askdirectory(title="Select Experiment Directory")
    if selected_directory:
        path = Path(selected_directory)
        print(f"Selected directory: {path}")
        return path
    else:
        print("No directory selected")
        sys.exit()

def gatherCSVs(dir, progress_bar, total_files):
    """
    Gathers all CSV files from the specified directory and its subdirectories, 
    reads them into pandas DataFrames, and concatenates them into a single DataFrame.
    Parameters:
    dir (Path): The directory to search for CSV files.
    progress_bar (tkinter.ttk.Progressbar): The progress bar widget to update as files are processed.
    total_files (int): The total number of files to process, used to calculate progress.
    Returns:
    pd.DataFrame: A concatenated DataFrame containing data from all CSV files found.
                  Returns an empty DataFrame if no CSV files are found.
    Raises:
    pd.errors.EmptyDataError: If a CSV file is empty.
    Exception: For any other errors encountered while reading a CSV file.
    """
    all_dfs = []
    processed_files = 0
    
    for folder in dir.iterdir():
        if folder.is_dir() and not folder.name.startswith('CombinedResults'):
            for file in folder.glob("*.csv"):
                try:
                    temp_df = pd.read_csv(file)
                except pd.errors.EmptyDataError:
                    print(f"Warning: {file} is empty, skipping...")
                    continue
                except Exception as e:
                    print(f"Error reading {file}: {e}")
                    continue
                temp_df['Sample'] = file.name
                patt = re.compile(r'(.*)_')
                temp_df['SampleGroup'] = patt.match(file.name[:-len('_results.csv')]).group(1)
                print("THRESH: ", positive_threshold)
                temp_df['Positive'] = temp_df['NumFoci'] >= positive_threshold
                all_dfs.append(temp_df)

                processed_files += 1
                progress_bar['value'] = (processed_files / total_files) * 100
                progress_bar.update()

    progress_window.destroy()
    return pd.concat(all_dfs) if all_dfs else pd.DataFrame()

def countCSVFiles(dir):
    """
    Counts the number of CSV files in the given directory and its subdirectories.

    Args:
        dir (Path): The directory path to search for CSV files.

    Returns:
        int: The total number of CSV files found in the directory and its subdirectories.
    """
    total_files = sum(1 for folder in dir.iterdir() if folder.is_dir() and not folder.name.startswith('CombinedResults') for file in folder.glob("*.csv"))
    return total_files

def detectSampleNames(dir):
    """
    Detects sample names from the directory.

    This function scans through the given directory and extracts sample names
    from folder names that match a specific pattern. It ignores folders that
    start with a dot ('.') or 'CombinedResults'.

    Args:
        dir (Path): The directory to scan for sample names.

    Returns:
        set: A set of unique sample names extracted from the folder names.
    """
    patt = re.compile(r'(.*)_')
    return {match.group(1) for folder in dir.iterdir() if not folder.name.startswith('.') and not folder.name.startswith('CombinedResults') for match in [patt.match(folder.name)] if match}

def confirmSampleNames(lista):
    """
    Displays a message box to confirm the detected sample names.

    Args:
        lista (list): A list of sample names to be confirmed.

    Returns:
        bool: True if the user clicks 'OK', False if the user clicks 'Cancel'.
    """
    message = '\n'.join(lista)
    return messagebox.askokcancel("", f"Confirm detected samples:\n\n{message}")

def getReplaceChoice(folder_name):
    """
    Prompt the user with a message box asking if they want to replace an old CombinedResults file.

    Parameters:
    folder_name (str): The name of the folder where the old CombinedResults file is located.

    Returns:
    bool or None: Returns True if the user chooses 'Yes', False if the user chooses 'No', 
                  and None if the user chooses 'Cancel'.
    """
    return messagebox.askyesnocancel("", f"Old CombinedResults found in this directory:\n\n({folder_name})\n\nWould you like to replace it?")

# def deleteDirectory():

def checkForOldCombinedResults(dir):
    """
    Checks for old combined results folders in the specified directory and prompts the user for action.

    Args:
        dir (Path): The directory to search for combined results folders.

    Iterates through each folder in the specified directory. If a folder name starts with "CombinedResults",
    the user is prompted to choose whether to delete and replace the folder. Based on the user's choice,
    the folder may be deleted and replaced, or the operation may be aborted.

    Prompts:
        - A message box asking if the user is sure they want to delete and replace the folder.

    Actions:
        - Deletes the folder if the user confirms.
        - Prints a message indicating the folder is being replaced.
        - Prints a message indicating the folder is not being replaced.
        - Aborts the operation if the user cancels.

    Raises:
        SystemExit: If the operation is aborted by the user.
    """
    for folder in dir.iterdir():
        if folder.is_dir() and folder.name.startswith('CombinedResults'):
            choice = getReplaceChoice(folder.name)
            if choice is True:
                if messagebox.askyesno("", f"Are you sure you want to delete and replace {folder.name}?"):
                    shutil.rmtree(folder)
                    # print(f"Replacing {folder.name}")
                else:
                    abort()
            elif choice is False:
                pass
                # print("Not replacing")
            elif choice is None:
                abort()

def abort():
    messagebox.showwarning("", f"Process aborted by user")
    sys.exit()

def createProgressBar():
    """
    Creates a progress bar window using Tkinter.

    This function creates a new top-level window with a title "Progress" and 
    a label indicating that CSV files are being processed. It also includes 
    a determinate progress bar with a length of 300 pixels.

    Returns:
        tuple: A tuple containing the progress window and the progress bar widget.
    """
    progress_window = tk.Toplevel()
    progress_window.title("Progress")
    label = tk.Label(progress_window, text="Processing CSV files...")
    label.pack(pady=10)
    progress_bar = ttk.Progressbar(progress_window, length=300, mode='determinate')
    progress_bar.pack(pady=20)
    return progress_window, progress_bar

def writeCombinedResults(combined_df, sample_list, directory):
    """
    Writes combined results to CSV files for each sample in the sample list.
    Parameters:
    combined_df (pd.DataFrame): The combined DataFrame containing all data.
    sample_list (list of str): List of sample names to filter the DataFrame.
    directory (str or Path): The directory where the results should be saved.
    The function creates a new directory named "CombinedResults_(YY.MM.DD-HH.MM)" 
    where YY.MM.DD is the current date and HH.MM is the current time. For each 
    sample in the sample list, it filters the combined DataFrame to include only 
    rows where the 'Sample' column contains the sample name. It then saves the 
    filtered DataFrame to a CSV file named "{sample}_results_combined.csv" in the 
    newly created directory. If no rows are found for a sample, it prints a message 
    indicating that no CSV files with the sample prefix were found. If the combined 
    DataFrame is empty, it prints an error message.
    """
    now = datetime.now()
    date_str = now.strftime("%y.%m.%d")
    time_str = now.strftime("%H.%M.%S")

    if not combined_df.empty:
        for sample in sample_list:
            filtered_df = combined_df[combined_df['Sample'].str.contains(sample, regex=False)]
            if not filtered_df.empty:
                new_dir = Path(directory) / f"CombinedResults_({date_str}-{time_str})"
                new_dir.mkdir(parents=True, exist_ok=True)
                
                filename = f"{sample}_results_combined.csv"
                file_path = new_dir / filename
                filtered_df.to_csv(file_path, index=False)
                print(f'Successfully created combined results file for: {sample}')
            else:
                print(f'No .csv files with "{sample}" prefix were found in this directory')
    else:
        print("ERROR: No .csv files found in directory")

def giveFeedback(total_files, sample_list):
    """
    Displays a message box with information about the process completion.

    The message box shows the number of files processed and the number of samples detected.

    Parameters:
    None

    Returns:
    None
    """
    messagebox.showinfo("", f"Process completed successfully\nFiles Processed: {total_files}\nSamples Detected: {len(sample_list)}\n")

def setPositiveThreshold(root):

    top = tk.Toplevel(root)
    top.title("Set Positive Threshold")
    top.geometry("400x200")

    frame=tk.Frame(top, padx=20, pady=20)
    frame.pack(expand=True)

    header_label=tk.Label(frame, text="Enter Threshold", font=("Helvetica 12 bold"))
    header_label.grid(row = 0, column=0, columnspan=2, pady=(0, 10))

    input_label=tk.Label(frame, text="Input threshold for cells\nto be considered positive", font=("Helvetica 10"))
    input_label.grid(row = 1, column=0, pady=(0, 10))

    entry= tk.Entry(frame, width= 20, font=("Helvetica 12"))
    entry.focus_set()
    entry.grid(row=1, column=1, pady=(0, 10), sticky='w')
    
    result = [None]
    
    def submit():    
        global positive_threshold
        positive_threshold = int(entry.get())
        top.destroy()
        result[0] = True

    def cancel():
        top.destroy()
        # messagebox.showwarning("", f"Process aborted by user")
        result[0] = False
        
    submit_button = tk.Button(frame, text="Submit", font=("Helvetica 12 bold"), bg="#679969", fg="white", command=submit, relief=tk.GROOVE)
    submit_button.grid(row=2, column=1, pady=10)
    submit_button = tk.Button(frame, text="Cancel", font=("Helvetica 12 bold"), bg="#A9A9A9", fg="white", command=cancel, relief=tk.GROOVE)
    submit_button.grid(row=2, column=0, pady=10)

    top.grab_set()
    root.wait_window(top)
    
    return result[0]

def plotResults(df, sample_list):
    """Plots the results of focus counts by sample."""
    global positive_threshold   
    summary_df = df.groupby('SampleGroup').agg(
        Positive=('Positive', 'sum'),
        Total=('Positive', 'size'),
        PctPositive=('Positive', lambda x: round((x.sum() / x.size) * 100, 2))
    ).reset_index()
    print(summary_df)

    sns.barplot(x='SampleGroup', y='NumFoci', data=df, capsize=0.1, hue='SampleGroup', palette='viridis')
    sns.stripplot(x='SampleGroup', y='NumFoci', data=df, hue='Positive', palette=({True : 'r', False : 'k'}), size=5, alpha=0.65)
    plt.xticks(rotation=45)
    plt.title('Focus Count by Sample')
    plt.ylabel('Count')
    plt.ylim(top=df['NumFoci'].max() + plt.ylim()[1] * 0.2)
    plt.xlabel(None)
    plt.legend('', frameon=False)
    plt.axhline(y=positive_threshold, color='r', linestyle='--')

    for sample in sample_list:
        pos_pct = summary_df[summary_df['SampleGroup'] == sample]['PctPositive'].iloc[0]
        plt.text(sample, plt.ylim()[1] - plt.ylim()[1] * 0.1,
                 f'% Positive: {pos_pct}\n({summary_df[summary_df["SampleGroup"] == sample]["Positive"].iloc[0]}/{summary_df[summary_df["SampleGroup"] == sample]["Total"].iloc[0]})',
                 color='k', ha='center')
    
    plt.tight_layout()
    plt.show()

def main():
    """Main function to run the program."""
    global progress_window
    global positive_threshold
    root = tk.Tk()
    root.withdraw()

    directory = selectDirectory()
    sample_list = detectSampleNames(directory)
    positive_threshold = 0

    checkForOldCombinedResults(directory)

    if not confirmSampleNames(sample_list):
        print("Check directory, aborting")
        sys.exit()

    total_files = countCSVFiles(directory)
    if total_files == 0:
        print("No CSV files found in directory")
        sys.exit()

    if not setPositiveThreshold(root):
        abort()
    progress_window, progress_bar = createProgressBar()
    combined_df = gatherCSVs(directory, progress_bar, total_files)

    writeCombinedResults(combined_df, sample_list, directory)
    giveFeedback(total_files, sample_list)
    plotResults(combined_df, sample_list)

if __name__ == "__main__":
    main()