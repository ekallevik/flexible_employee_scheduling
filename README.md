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

Run PALNS
```python main.py --problem=PROBLEM_NAME --nowith_sdp run_alns```

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

## Problem Fixes.
As we encountered some difficulties regarding some of the provided problems a few special fixes was done to address the problems. In some cases it only affects the parameters used when running the problem. However, in one case we had to do some changes to the code.

### rproblem4 fix
For rproblem4 the parameter defining which day a shift belongs to is changed from 24 (regular calendar days) to 20. A shift begining at 20:00 or later is then defined to belong to the next day. This parameter affects the constraint saying an employee are only allowed to work one shift each day. 

Changing this parameter had unforseen impact on some of the implemented repair operators. The MIP model is on the other hand intact, and works as usual. 
Some of the repair operators check if an employee works a shift on a particular day, creating a set of available employees. However, the calculation relied on the day_defining_shift parameter to stay at 24. To fix this the following code:
```shifts_at_day[int(shift[0] / 24)]```
was replaced with:
```shifts_at_day[min(83,int((shift[0] + 4) / 24))]```
