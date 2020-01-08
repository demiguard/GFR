# GFR
GitHub repository for code running http://gfr.petnet.rh.dk

For installation, deployment and running the code consult the file: doc/install.md

---

## Running tests
The following script will run the tests and generate reports using ```coverage.py```. The reports are ```xml``` files and can be interpreted with e.g. the VS Code extension; Coverage Gutter
```
(venv)> ./run-tests.sh
```

The script comes with help information for more advanced usage:
```
(venv)> ./run-tests.sh --help
```

Remember to make the script executable using:
```
(venv)> chmod a+x ./run-tests.sh
```
