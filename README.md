To convert this in to a standalone and installable console app, use a tool like PyInstaller. This process bundles your script, the Python interpreter, and all its dependencies into a single executable file or a folder of files. You can then run this executable without needing to have Python installed on their machine.

Step 1: Install PyInstaller
First, you need to install PyInstaller using pip, the Python package manager. Open your terminal or command prompt and run the following command:

pip install pyinstaller

This will download and install the PyInstaller package and its dependencies.

Step 2: Create the Executable
Once PyInstaller is installed, navigate to the directory where your Python script is saved. For this example, let's assume your script is named my_app.py. To convert it into a console application, run PyInstaller with the --onefile and --console flags.

pyinstaller --onefile --console my_app.py

The --onefile flag bundles all the code and dependencies into a single executable file. Without this flag, PyInstaller creates a directory containing the executable and a library of files.

The --console (or -c) flag ensures that a console window opens when the application is run, which is necessary for a console app to display output and accept input.

After running the command, PyInstaller will create a new directory named dist in your current folder. Inside the dist directory, you'll find your new executable file (e.g., my_app.exe on Windows or my_app on macOS/Linux).

Here are the command-line interface (CLI) references for your app.

Command Structure
The general command structure for using your application from the CLI is as follows:

cleanup_app.exe --cli [options]
The --cli flag is required to bypass the graphical user interface (GUI) and activate the command-line functionality.

Available Flags
Flag	Description
--help	Displays the help menu with all available options and their descriptions. This flag can be used without the --cli flag.
--cli	Activates the command-line interface mode, preventing the GUI from launching.
--analyze	Runs the application in analysis mode. When used with other cleanup flags, it will calculate potential space savings for the selected tasks instead of performing the cleanup.
--all	A shortcut flag that selects all available cleanup tasks.
--temp	Selects the "Clean Temporary Files" task.
--trash	Selects the "Empty Recycle Bin / Trash" task.
--cache	Selects the "Clean System & Browser Caches" task.
--prefetch	Selects the "Clean Prefetch Files" task. This option is only effective on Windows.
--defrag	Selects the "Defragment Disk" task. This option is only effective on Windows HDDs.
--large-old	Selects the "Find Large & Old Files" task.
--empty-dirs	Selects the "Remove Empty Directories" task.
