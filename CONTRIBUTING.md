# Contribution Guide

## How to Contribute
Almost all communication with the SatPlot maintainers should be done through the main SatPlot Gitlab repository: https://gitlab.unimelb.edu.au/msl/tools/satplot

- Bug reports and feature requests can be submitted through the “Issues” page on the repository. It is critical that sufficient information is provided in the bug report to recreate the problem. Please provide:
  - The SatPlot version number, which can be found from the `About` toolbar menu, or printed on the command line when the application first opens.
  - Attach any data files in which the bug was evident: save file, source data files, etc.
  - A description of the behaviour.

- Any changes to actual code, including documentation, should be submitted as a merge request on Gitlab.
  - Please make sure to submit merge requests using a new branch following the [Branch Naming Convention](#branch-naming-convention). Don’t be afraid to create a merge request as soon as the branch is created. It can be always be updated later. Creating them early gives maintainers a chance to provide an early review of your code if that’s something you’re looking for. See below for more information on writing documentation and checking your changes.
  - Make sure you understand the overall architecture of SatPlot before adding features.
	- A description of the architecture can be found in the [ARCHITECTURE.md](https://gitlab.unimelb.edu.au/msl/tools/satplot/-/blob/main/ARCHITECTURE.md) file

- No matter how you contribute, SatPlot maintainers will try their best to read, research, and respond to your query as soon as possible. For code changes, automated checks and tests will run on Gitlab to provide an initial “review” of your changes.

## Submitting Bugs
Please submit problems or bus as issues in gitlab,

https://gitlab.unimelb.edu.au/msl/tools/satplot/-/issues

## Submitting Feature Ideas
Please submit feature ideas as an issue in gitlab, 

https://gitlab.unimelb.edu.au/msl/tools/satplot/-/issues

## Asking Questions
Please submit questions as an issue in gitlab,

https://gitlab.unimelb.edu.au/msl/tools/satplot/-/issues

## Adding Features
### Branch Naming Convention

## Development Environment
It is recommended that you setup a virtual environment running python 3.10 or later, and install the packages required within that virtual environment using
```
pip install -r requirements.txt
```

## Coding Style
In general, SatPlot follows the PEP 8 style guidelines:

https://www.python.org/dev/peps/pep-0008/

The easiest way to see if your meeting these guidelines is to code as you normally would and run `flake8` to check for errors (see below). Otherwise, see existing SatPlot code for examples of what is expected.


### Checking Coding Style
Code style is automatically checked by SatPlot’s Continuous Integration (CI). If you’d like to check the style on your own local machine you can install and run the flake8 utility from the root of the SatPlot repository. To install:
```
pip install flake8
```
Then run the following from the root of the SatPlot directory:
```
python make test flake
```
This will inform you of any code style issues in the entire SatPlot python package directory.

## Documentation Style
All docstrings in SatPlot python code follow the NumPy style. You can find the full reference here:

https://numpydoc.readthedocs.io/en/latest/format.html

However, the simplest method is to copy existing doc strings and modify as required.

### Checking Documentation Style
Similar to code style, documentation style is tested during SatPlot's automated testing when you create or edit a merge request. If you’d like to check it locally you can use the same flake8 tool as for code, but with the addition of the flake8-docstring package. To install:
```
pip install flake8-docstrings
```
Then run the following from the root of the SatPlot directory
```
python make test flake
```
This will check both code style and doscstring style


## Testing
SatPlot depends on self-contained tests to know that changes haven’t broken any existing functionality. Our unit tests are written using the `pytest` library. Some parts of SatPlot require extra steps to test them thoroughly, but utilities exist to help with this. For example, SatPlot can utilise multiple backends and backend settings depending on command line options. So to be thoroughly checked tests should be run for each of these backends. Luckily, SatPlot’s automated tests will run every test over a series of backends for you when you make a merge request so you shouldn’t normally have to worry about this in your local testing.

### Writing Tests

### Running Tests