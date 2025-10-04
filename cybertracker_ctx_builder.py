#!/usr/bin/env python3
"""
CyberTracker CTX File Builder
Rebuilds .ctx files from their constituent .xml, .txt, and .dat components
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import List, Tuple, Optional
import sys


class CTXBuilder:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CyberTracker CTX Builder")
        self.root.geometry("600x400")
        self.root.resizable(False, False)

        # Variables
        self.selected_directory = tk.StringVar()
        self.file_sets = []
        self.selected_set_index = None

        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(main_frame, text="CyberTracker CTX File Builder",
                                font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Directory selection
        dir_frame = ttk.LabelFrame(main_frame, text="Step 1: Select Directory", padding="10")
        dir_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        self.dir_label = ttk.Label(dir_frame, textvariable=self.selected_directory,
                                   relief="sunken", anchor="w")
        self.dir_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        dir_frame.columnconfigure(0, weight=1)

        browse_btn = ttk.Button(dir_frame, text="Browse...", command=self.browse_directory)
        browse_btn.grid(row=0, column=1)

        # File sets selection
        sets_frame = ttk.LabelFrame(main_frame, text="Step 2: Select File Set", padding="10")
        sets_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        main_frame.rowconfigure(2, weight=1)

        # Listbox with scrollbar
        list_frame = ttk.Frame(sets_frame)
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        sets_frame.rowconfigure(0, weight=1)
        sets_frame.columnconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        self.sets_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.sets_listbox.yview)

        self.sets_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        self.sets_listbox.bind('<<ListboxSelect>>', self.on_set_select)

        # Info label
        self.info_label = ttk.Label(sets_frame, text="No file sets found", foreground="gray")
        self.info_label.grid(row=1, column=0, pady=(5, 0))

        # Build button
        self.build_btn = ttk.Button(main_frame, text="Build CTX File",
                                    command=self.build_ctx, state="disabled")
        self.build_btn.grid(row=3, column=0, columnspan=2, pady=(10, 0))

        # Status bar
        self.status_label = ttk.Label(main_frame, text="Select a directory to begin",
                                      relief="sunken", anchor="w")
        self.status_label.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

    def browse_directory(self):
        """Open directory selection dialog"""
        directory = filedialog.askdirectory(title="Select Directory Containing CTX Components")
        if directory:
            self.selected_directory.set(directory)
            self.scan_for_file_sets(directory)

    def scan_for_file_sets(self, directory: str):
        """Scan directory for sets of .xml, .txt, and .dat files"""
        self.file_sets = []
        self.sets_listbox.delete(0, tk.END)

        # Find all relevant files
        xml_files = []
        txt_files = []
        dat_files = []

        for file in Path(directory).iterdir():
            if file.is_file():
                lower_name = file.name.lower()
                if lower_name.endswith('.xml'):
                    xml_files.append(file)
                elif lower_name.endswith('.txt'):
                    txt_files.append(file)
                elif lower_name.endswith('.dat'):
                    dat_files.append(file)

        # Try to match file sets based on base names
        processed_files = set()

        for xml_file in xml_files:
            if xml_file in processed_files:
                continue

            base_name = xml_file.stem
            txt_match = None
            dat_match = None

            # Look for matching txt and dat files
            for txt_file in txt_files:
                if txt_file.stem.lower() == base_name.lower():
                    txt_match = txt_file
                    break

            for dat_file in dat_files:
                if dat_file.stem.lower() == base_name.lower():
                    dat_match = dat_file
                    break

            if txt_match and dat_match:
                self.file_sets.append({
                    'name': base_name,
                    'xml': xml_file,
                    'txt': txt_match,
                    'dat': dat_match
                })
                processed_files.update([xml_file, txt_match, dat_match])

        # Update UI
        if self.file_sets:
            for i, file_set in enumerate(self.file_sets):
                display_text = f"{file_set['name']} (.xml, .txt, .dat)"
                self.sets_listbox.insert(tk.END, display_text)

            self.info_label.config(text=f"Found {len(self.file_sets)} complete file set(s)")
            self.status_label.config(text=f"Found {len(self.file_sets)} file set(s). Select one to build.")
        else:
            self.info_label.config(text="No complete file sets found (need matching .xml, .txt, .dat files)")
            self.status_label.config(text="No complete file sets found in this directory")
            self.build_btn.config(state="disabled")

    def on_set_select(self, event):
        """Handle file set selection"""
        selection = self.sets_listbox.curselection()
        if selection:
            self.selected_set_index = selection[0]
            self.build_btn.config(state="normal")
            self.status_label.config(text=f"Selected: {self.file_sets[self.selected_set_index]['name']}")
        else:
            self.selected_set_index = None
            self.build_btn.config(state="disabled")

    def build_ctx(self):
        """Build the CTX file from selected file set"""
        if self.selected_set_index is None:
            messagebox.showerror("Error", "Please select a file set first")
            return

        file_set = self.file_sets[self.selected_set_index]

        try:
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Copy and rename files
                self.status_label.config(text="Copying and renaming files...")
                self.root.update()

                shutil.copy2(file_set['xml'], temp_path / "Info.xml")
                shutil.copy2(file_set['txt'], temp_path / "Elements.txt")
                shutil.copy2(file_set['dat'], temp_path / "Sightings.DAT")

                # Create CAB file
                self.status_label.config(text="Creating CAB file...")
                self.root.update()

                cab_file = temp_path / f"{file_set['name']}.cab"

                # Create DDF file for makecab
                ddf_content = f""".OPTION EXPLICIT
.Set CabinetNameTemplate={file_set['name']}.cab
.Set DiskDirectoryTemplate=
.Set CompressionType=MSZIP
.Set Cabinet=ON
.Set Compress=ON
.Set CabinetFileCountThreshold=0
.Set FolderFileCountThreshold=0
.Set FolderSizeThreshold=0
.Set MaxCabinetSize=0
.Set MaxDiskFileCount=0
.Set MaxDiskSize=0
"Info.xml"
"Elements.txt"
"Sightings.DAT"
"""
                ddf_file = temp_path / "directive.ddf"
                ddf_file.write_text(ddf_content)

                # Run makecab
                try:
                    # Change to temp directory for makecab
                    original_dir = os.getcwd()
                    os.chdir(temp_path)

                    result = subprocess.run(
                        ["makecab", "/F", "directive.ddf"],
                        capture_output=True,
                        text=True,
                        check=True
                    )

                    os.chdir(original_dir)

                except subprocess.CalledProcessError as e:
                    messagebox.showerror("Error", f"Failed to create CAB file:\n{e.stderr}")
                    return
                except FileNotFoundError:
                    messagebox.showerror("Error",
                                         "makecab.exe not found. Please ensure you're running this on Windows.")
                    return

                # Rename to .ctx
                self.status_label.config(text="Creating CTX file...")
                self.root.update()

                output_dir = Path(self.selected_directory.get())
                ctx_file = output_dir / f"{file_set['name']}.ctx"

                # Check if file exists
                if ctx_file.exists():
                    if not messagebox.askyesno("File Exists",
                                               f"{ctx_file.name} already exists. Overwrite?"):
                        self.status_label.config(text="Operation cancelled")
                        return

                # Copy cab file with .ctx extension
                shutil.copy2(cab_file, ctx_file)

                # Success message
                self.status_label.config(text=f"Successfully created {ctx_file.name}")
                messagebox.showinfo("Success",
                                    f"Done! The file is located here:\n{ctx_file}\n\n"
                                    "Import into the appropriate CyberTracker database.")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
            self.status_label.config(text="Error occurred during build")

    def run(self):
        """Start the application"""
        self.root.mainloop()


def main():
    """Main entry point"""
    # Check if running on Windows
    if sys.platform != 'win32':
        response = messagebox.askyesno("Platform Warning",
                                       "This program is designed for Windows (uses makecab.exe).\n"
                                       "It may not work correctly on your current platform.\n\n"
                                       "Continue anyway?")
        if not response:
            return

    app = CTXBuilder()
    app.run()


if __name__ == "__main__":
    main()