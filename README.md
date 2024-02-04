# Game Server and Client Setup Instructions

Before attempting to run the game, please ensure the following prerequisites are met:

## Prerequisites
1. **Python Installation**: Ensure that Python is installed on your machine.
2. **Required Libraries**: Install any libraries necessary for running the files. The specific libraries required should be listed in a 'requirements.txt' file.
  For **python libraries** (you dont have to download it): **threading** , **socket** , **time** , **multiprocessing** , **copy**.
  For **non-python library** (you may need to download it): **random**

3. **Python Files**: Download all the required Python files and place them within the same directory.

## Launching the Game
You will need to launch a number of clients corresponding to the number of players (either 2 or 3, default 2) and a single server. You must start the client after starting the server. After enough people connect to the server, the game will automatically start. There are multiple ways to start the game:

**Using a Code Editor (e.g., VSCode)**
- Open the server and client files in your code editor and run them within the editor's integrated terminal.

**Using Terminal**
- Open multiple terminal windows and execute the code. For Linux systems, the commands would be as follows:
  ```bash
  /bin/python3 game_process.py          # For the server
  /bin/python3 game_process_client.py   # For each client
  ```

## Important Notes
- **Port Availability**: If you run into issues where the port is already in use, you may experience a hang. If this occurs, interrupt the process using 'Ctrl+C' and attempt to run the script again after a short while.
