# Flexible Employee Scheduling
Code for Master Thesis at NTNU

# How to run the code
1. Navigate to ../flexible employee scheduling/
2. Run one of the available commands. This will initiate one of the methods from the
 ProblemRunner-class

## Available commands

Run any method with arguments ARGS by using:
``python main.py FUNCTION_NAME ARGS```
    
Run methods in a chain:
```python main.py INIT_ARGS FUNC1 --FUNC1_ARG=FUNC1_VALUE - FUNC2 --FUNC2_ARG=FUNC2_VALUE```
    
Note1: only functions that return `self` can be chained.
Note2: functions has to be separated by `-`

Access property PROP by using: 
```python main.py FUNCTION_NAME PROP```

## Examples
Initialize object with default arguments 
```python main.py```
    
Run ESP with SDH-SR
```python main.py --problem=PROBLEM_NAME run_esp```
    
Run ESP with SDH (without SR)
```python main.py --problem=PROBLEM_NAME --with_sdp=False run_esp```

Run PALNS with SDH-SR
```python main.py --problem=PROBLEM_NAME run_palns```

Run PALNS with SDH (without SR)
```python main.py --problem=PROBLEM_NAME --with_sdp=False run_palns```

Note1, the MIP model from the report is named `ESP` in the code. 

## Problem names
* P1 - rproblem1
* P2 - rproblem2
* P3 - rproblem3
* P4 - rproblem4
* P5 - rproblem5
* P6 - rproblem6
* P7 - rproblem7
* P8 - rproblem8
* P9 - rproblem9