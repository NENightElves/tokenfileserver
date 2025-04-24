# Token File Server
Token File Server is a simple file server written by python.

## Installation
You can simply clone the repository or just download the `main.py` file.
The requirements are in the `requirements.txt` file. You can install requirements by running:
```
pip3 install -r requirements.txt
```
or just run:
```
pip3 install flask==3.1.0
```

## Usage
The usage of the script can be found by running:
```
python3 main.py --help
```
The typical usage of the script is as follows:
```
python3 main.py -f files -p 5000 --init
```
- `-f` will specify the directory where the files will be stored.
- `-p` will specify the port the server will listen on.
- `--init` will force to initialize the database.

Then you can visit `http://localhost:5000/apidocs` to get the API documentation.
