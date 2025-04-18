# Welcome to gs2py!
## Introduction
gs2py aims to aid gs2 automation and data processing in python.
More information on gs2 can be found here: https://gyrokinetics.gitlab.io/gs2/page/index.html
## User guide
This section is still under work
### Class converge
```python
gs2py.converge(pyro, tolerance, gs2_directory, max)
````
The converge object is used to run simulations until a specified measurement is within a percentage tolerance. This can be particularly useful for calibrating grid resolution (ntheta).

Arguments:
* pyro: *pyrokinetics pyro object*.
* tolerance: *float*, defines the accuracy of the convergance.
* gs2_directory: *path, default="~/gs2/bin/gs2"*, contains gs2 directory.
* max: *int, default=100*, maximum number of runs before terminating. Prevents errors in case the scenario does not converge.

#### converge.run
```python
converge.run(param_name, measure_name, param_initial_value, param_increment, save_results, graph)
````
Runs the convergance for the specified quantity.

Arguments:
* param_name: *str*, parameter being changed.
* measure_name: *str*, quantity being converged.
* param_initial_value: *float/int*, starting value of the parameter.
* param_increment: *float/int*, ammount the parameter will be incremented by.
* save_results: *bool, default=True* determines whether results are saved or deleted.
* graph: *bool, default=False* determines whether results will be outputted as a graph or raw data.
### Class scan
```python
gs2py.scan(pyro,gs2_directory)
````
The scan object is used to run gs2 simulations over a range of inputs.
Arguments:
* pyro: *pyrokinetics pyro object*.
* gs2_directory: *path, default="~/gs2/bin/gs2"*, contains gs2 directory.
#### scan.run
````python
scan.run(param_name, measure_names, initial, final, increment, save_results, folder_name, new_folder, smart, cap, smart_data)
````
Performs the scan over a range of input parameters.

Aruguments:
* param_name: *str*, parameter being changed.
* measure_names: *list*, list of data to measured from the GS2 runs.
* initial: *int/float*, parameter starting value.
* final: *int/float*, parameter ending value.
* increment: *int/float*, the amount the parameter is incremented by.
* save_results: *bool, default=True*, determines whether results are saved or deleted.
* folder_name: *str, default=""*, if not changed, gs2py will automatically name the folder containing the data.
* new_folder: *str, default=True*, if false, will save data to folder folder_name.
* smart: *bool, default=False*, allows for smart scanning, which locates areas lacking data points and carries out more GS2 runs.
* cap: *int, default=4*, only used for smart scans. Limits the recursion of the algorithm to save resources.
* smart_data: *list, default=[0,0,0,0]*, data used for the smart scan recursive algorithm. Do not change this unless you know what you're doing.

Returns:
* data object
#### scan.smart_scan
````python
scan.smart_scan(scan_data,cap, smart_data, folder_name)
````
Recursive function called by scan.run when smart_scan=True. Can be called manually to improve data inside a data object.

Arguments:
* scan_data: *data object*
* cap: *int, default=4*, limits the recursion of the algorithm to save resources.
* smart_data: *list*, data in the form [recursion level, standard deviation, mean, index of measurement within data.measure_data].
* folder_name: *str*, folder to save the new run data to.

Returns:
* data object

### Class data
#### print
#### new_load
#### load
#### mult_load
#### sort
#### graph
