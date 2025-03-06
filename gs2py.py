class converge:

    def __init__(
            self,
            pyro="",           # pyro object
            tolerance=0.05,
            gs2_directory="~/gs2/bin/gs2",
            debug=False,
            end=100     # max number of simulations before force quitting
    ):
        # stores the pyro object
        self.pyro = pyro
        # % difference between outputs to be considered 'converged'
        self.tolerance = tolerance
        # gs2 directory
        self.gs2_directory = gs2_directory
        # debug mode
        self.debug = debug
        # max number of simulations before force quitting
        self.end = end


    def run(
            self,
            param_name="",              # parameter being changed
            param_initial_value=50,     # parameter initial value
            param_initial_increment=10, # parameter initial variance increment
            measure_name="",            # quantity being measured
            save_results=False,         # whether results are saved
            graph=False                 # whether results are displayed in a graph
    ):
        input_file = self.pyro.gk_file

        #   for debugging only
        if self.debug:
            param_name = "ntheta"
            measure_name = "gamma"

        param_list = []     # stores parameter values for each run
        measure_list = []   # stores calculated values for each run
        param_value = param_initial_value - param_initial_increment     # sets initial parameter
        param_increment = param_initial_increment   # sets initial increment

        # file management
        with open(input_file, "r") as file:     # opens input file

            # creates folder to contain outputs
            j = 1
            while j > 0:    # creates a uniquely numbered directory
                if os.path.exists(f"gs2py_converge_{j}"):
                    j += 1
                else:
                    j = -j
            subprocess.run(f"mkdir gs2py_converge_{-j}", shell=True)

            # begins loop of gs2 runs
            end = False
            i = 0   # number of runs
            while not end:
                if i > self.end:
                    end = True
                param_value += param_increment

                # create new gs2 input file with altered parameter
                with open(f"gs2py_converge_{-j}//{param_value}.in", "w") as newfile:
                    file.seek(0)
                    for line in file:
                        match = re.search(f"{param_name} = ", line)
                        if match:
                            newline = f"  {param_name} = {param_value}\n"
                            newfile.write(line.replace(line, newline))
                        else:
                            newfile.write(line)
                newfile.close()

                param_list.append(param_value) # records current parameter value

                # runs gs2
                subprocess.run(f"mpirun -np 4 ~/gs2/bin/gs2 gs2py_converge_{-j}/{param_value}.in",
                               shell=True)

                # data processing
                ds = xarray.open_dataset(f"gs2py_converge_{-j}/{param_value}.out.nc")

                # obtains final growth rate values
                if measure_name == "gamma":
                    measure_value = ds.omega.isel(ri=1, t=-1).values
                else:
                    print("Error: invalid measure_name")
                    return
                measure_list.append(measure_value[0][0])

                if self.debug:
                    print(f"Ran gs2 for {param_name} = {param_value}")
                    print(f"{measure_name} = {measure_value[0][0]}")
                    print(f"{measure_name} percentage difference = " +
                          str(np.abs(measure_list[i] - measure_list[i - 1]) / measure_list[i])
                          + "%")

                # performs run comparisons
                if i > 0:
                    if np.abs(measure_list[i] - measure_list[i-1])/measure_list[i] < self.tolerance:
                        end = True

                        # data output
                        print(f"Converged {measure_name} to " +
                        str(np.abs(measure_list[i] - measure_list[i - 1]) / measure_list[i])
                        + "%")
                        print(f"Optimal {param_name} value is {param_value}")
                i += 1

            # deleting temporary files
            if not save_results:
                subprocess.run(f"rm -r gs2py_converge_{-j}", shell=True)
            file.close()

        # graphing results
        if graph:
            plt.plot(param_list, measure_list, linestyle="", marker="+", markersize=5)
            plt.ylabel(r"growth rate $\gamma$")
            plt.xlabel("ntheta")
            plt.show(block=True)



class scan:

    def __init__(
            self,
            pyro="",           # pyro object
            gs2_directory="~/gs2/bin/gs2",
            debug=False,
    ):
        # stores the pyro object
        self.pyro = pyro
        # gs2 directory
        self.gs2_directory = gs2_directory
        # debug mode
        self.debug = debug

    def run(
            self,
            param_name="",              # parameter being varied
            param_initial_value=0,      # parameter initial value
            param_final_value=1,        # parameter final value
            param_initial_increment=1,  # parameter increment
            measure_names=[],           # quantities being measured
            save_results=True,          # whether results are saved
            graph=False  # whether results are displayed in a graph
    ):
        input_file = self.pyro.gk_file

        #   for debugging only
        if self.debug:
            param_name = "beta"
            measure_names = ["gamma"]

        param_list = []  # stores parameter values for each run
        measure_list = [[]]  # stores calculated values for each run
        i = 1
        while i < len(measure_names):
            measure_list.append([])
            i += 1

        param_value = param_initial_value - param_initial_increment  # sets initial parameter
        param_increment = param_initial_increment  # sets initial increment

        # file management
        with open(input_file, "r") as file:  # opens input file

            # creates folder to contain outputs
            j = 1
            while j > 0:  # creates a uniquely numbered directory
                if os.path.exists(f"gs2py_{param_name}_scan_{j}"):
                    j += 1
                else:
                    j = -j
            subprocess.run(f"mkdir gs2py_{param_name}_scan_{-j}", shell=True)

            # begins loop of gs2 runs
            end = False
            while not end:
                if param_value >= param_final_value:
                    end = True
                param_value += param_increment

                # create new gs2 input file with altered parameter
                with open(f"gs2py_{param_name}_scan_{-j}//{param_value}.in", "w") as newfile:
                    file.seek(0)
                    for line in file:
                        match = re.search(f"{param_name} = ", line)
                        if match:
                            newline = f"  {param_name} = {param_value}\n"
                            newfile.write(line.replace(line, newline))
                        else:
                            newfile.write(line)
                newfile.close()

                param_list.append(param_value) # records current parameter value

                # runs gs2
                subprocess.run("mpirun -np 4 "
                               f"~/gs2/bin/gs2 gs2py_{param_name}_scan_{-j}/{param_value}.in",
                               shell=True)

                # data processing
                ds = xarray.open_dataset(f"gs2py_{param_name}_scan_{-j}/{param_value}.out.nc")

                k = 0
                while k < len(measure_names):

                    # obtains final growth rate values
                    if measure_names[k] == "gamma":
                        measure_value = ds.omega.isel(ri=1, t=-1).values
                    else:
                        print("Error: invalid measure_name")
                        return
                    measure_list[k].append(measure_value[0][0])
                    k += 1

                if self.debug:
                    print(f"Ran gs2 for {param_name} = {param_value}")
                    print(f"{measure_names[0]} = {measure_value[0][0]}")

            # deleting temporary files
            if not save_results:
                subprocess.run(f"rm -r gs2py_{param_name}_scan_{-j}", shell=True)
            file.close()

            print(measure_names)
            print(measure_list)

            if graph:   # plots results on a graph
                i = 0
                while i < len(measure_list):

                    if len(measure_names) > 100:
                        marker_size = 3
                    elif len(measure_names) > 20:
                        marker_size = 8
                    else:
                        marker_size = 10
                    plt.plot(param_list, measure_list[i], linestyle="",
                             marker="+", markersize=marker_size)
                    if measure_names[i] == "gamma":
                        plt.ylabel(r"$\gamma$")
                    if param_name == "beta":
                        plt.xlabel("$\\beta$")
                    plt.show(block=True)
                    i += 1
