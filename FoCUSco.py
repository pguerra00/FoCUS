from pathlib import Path
import pandas as pd
import re
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, ttk
from datetime import datetime
import shutil

def selectDirectory():
    # root = tk.Tk()
    # root.withdraw()

    selected_directory = filedialog.askdirectory(title="Select Experiment Directory")

    if selected_directory:
        path = Path(selected_directory)
        print(f"Selected directory: {path}")
        return path
    else:
        print("No directory selected")
        quit()

def gatherCSVs(dir, progress_bar, total_files):
    all_dfs = []
    processed_files = 0
    
    for folder in dir.iterdir():
        if folder.is_dir():
            for file in folder.glob("*.csv"):
                temp_df = pd.read_csv(file)
                temp_df['Sample'] = file.name
                all_dfs.append(temp_df)

                processed_files += 1
                progress_bar['value'] = (processed_files / total_files) * 100
                progress_bar.update()

                if progress_bar['value'] == 100:
                    progress_window.destroy()

    return pd.concat(all_dfs) if all_dfs else pd.DataFrame()

def countCSVFiles(dir):
    total_files = sum(1 for folder in dir.iterdir() if folder.is_dir() for file in folder.glob("*.csv"))
    return total_files

def detectSampleNames(dir):
    patt = re.compile(r'(.*)_')
    return {match.group(1) for folder in dir.iterdir() if not folder.name.startswith('.') and not folder.name.startswith('CombinedResults') for match in [patt.match(folder.name)] if match}

def confirmSampleNames(lista):
    message = '\n'.join(lista)
    return messagebox.askokcancel("", f"Confirm detected samples:\n\n{message}")

def getReplaceChoice(folder_name):
    return messagebox.askyesnocancel("", f"Old CombinedResults found in this directory:\n\n({folder_name})\n\nWould you like to replace it?")

def checkForOldCombinedResults(dir):
    for folder in dir.iterdir():
        if folder.is_dir():
            if folder.name.startswith("CombinedResults"):
                choice = getReplaceChoice(folder.name)
                if choice is True:
                    confirmation = messagebox.askyesno("", f"Are you sure you want to delete and replace {folder.name}?")
                    if confirmation is True:
                        shutil.rmtree(folder)
                        print(f"Replacing {folder.name}")
                    else:
                        print("Not replacing")
                        quit()
                elif choice is False:
                    print("Not replacing")
                elif choice is None:
                    print("Aborting")
                    quit()

def createProgressBar():
    progress_window = tk.Toplevel()
    progress_window.title("Progress")
    label = tk.Label(progress_window, text="Processing CSV files...")
    label.pack(pady=10)
    progress_bar = ttk.Progressbar(progress_window, length=300, mode='determinate')
    progress_bar.pack(pady=20)
    return progress_window, progress_bar

root = tk.Tk()
root.withdraw()
directory = selectDirectory()
sample_list = detectSampleNames(directory)

checkForOldCombinedResults(directory)

correct_samples = confirmSampleNames(sample_list)
if not correct_samples:
    print("Check directory, aborting")
    quit()

total_files = countCSVFiles(directory)
if total_files == 0:
    print("No CSV files found in directory")
    quit()

progress_window, progress_bar = createProgressBar()
combined_df = gatherCSVs(directory, progress_bar, total_files)

def main():
    now = datetime.now()
    date_str = now.strftime("%y%m%d")
    time_str = now.strftime("%H-%M")

    if not combined_df.empty:
        for sample in sample_list:
            filtered_df = combined_df[combined_df['Sample'].str.contains(sample, regex=False)]
            if not filtered_df.empty:
                new_dir = directory / f"CombinedResults_({date_str}_{time_str})"

                filename = f"{sample}_results_combined.csv"
                new_dir.mkdir(parents=True, exist_ok=True)
                file_path = new_dir / filename
                filtered_df.to_csv(file_path, index=False)

                print(f'Successfully created combined results file for: {sample}')
                
            else:
                print(f'No .csv files with "{sample}" prefix were found in this directory')
    else:
        print("ERROR: No .csv files found in directory")

    input("Program finished without errors, press enter to exit...") 
    root.destroy()

if __name__ == "__main__":
    main()