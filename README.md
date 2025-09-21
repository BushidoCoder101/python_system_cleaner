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
