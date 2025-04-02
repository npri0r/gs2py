def edit(
        pyro,
        param,
        value,
):
    # stores pyro object
    pyro = pyro
    # stores parameter name and new value
    param = param
    value = value

    # alters the value of the parameter
    subprocess.run(f"sed -i 's/{param} = .*/{param} = {value}/g' {pyro.gk_file}", shell=True)


class converge:

    def __init__(
            self,
            pyro,  # pyro object
            tolerance=0.05,
            gs2_directory="~/gs2/bin/gs2",
            debug=False,
            max=100 # max number of simulations before force quitting
    ):
        # stores the pyro object
        self.pyro = pyro
        # % difference between outputs to be considered 'converged'
        self.tolerance = tolerance
        # gs2 directory
        self.gs2_directory = gs2_directory
        # debug mode
        self.debug = debug
        # max number of simulations
        self.max = max

    def run(
            self,
            param_name="",  # parameter being changed
            param_initial_value=50,  # parameter initial value
            param_initial_increment=10,  # parameter initial variance increment
            measure_name="",  # quantity being measured
            save_results=False,  # whether results are saved
            graph=False  # whether results are displayed in a graph
    ):
        input_file = self.pyro.gk_file

        #   for debugging only
        if self.debug:
            param_name = "ntheta"
            measure_name = "gamma"

        param_list = []  # stores parameter values for each run
        measure_list = []  # stores calculated values for each run
        param_value = param_initial_value - param_initial_increment  # sets initial parameter
        param_increment = param_initial_increment  # sets initial increment
        runtime_list = []   # stores runtime_list

        # file management
        with open(input_file, "r") as file:  # opens input file

            # creates folder to contain outputs
            j = 1
            while j > 0:  # creates a uniquely numbered directory
                if os.path.exists(f"gs2py_converge_{j}"):
                    j += 1
                else:
                    j = -j
            subprocess.run(f"mkdir gs2py_converge_{-j}", shell=True)

            # begins loop of gs2 runs
            end = False
            i = 0  # number of runs
            while not end:
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

                param_list.append(param_value)  # records current parameter value

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

                with open(f"gs2py_converge_{-j}//{param_value}.timing_stats", "r") as newfile:
                    newfile.seek(0)
                    for line in newfile:
                        match = re.search("Total", line)
                        if match:
                            times = re.split("\\s+", line)
                            runtime_list.append(times[3])
                newfile.close()


                if self.debug:
                    print(f"Ran gs2 for {param_name} = {param_value}")
                    print(f"{measure_name} = {measure_value[0][0]}")
                    print(f"{measure_name} percentage difference = " +
                          str(np.abs(measure_list[i] - measure_list[i - 1]) / measure_list[i])
                          + "%")
                    print(f"Runtime: {times[3]}")

                # performs run comparisons
                if i > 0:
                    if np.abs(measure_list[i] - measure_list[i - 1]) / measure_list[i] < self.tolerance:
                        end = True

                        # data output
                        print(f"Converged {measure_name} to " +
                              str(np.abs(measure_list[i] - measure_list[i - 1]) / measure_list[i])
                              + "%")
                        print(f"Optimal {param_name} value is {param_value}")
                elif i > self.max:
                    end = True
                i += 1

            # deleting temporary files
            if not save_results:
                subprocess.run(f"rm -r gs2py_converge_{-j}", shell=True)
            file.close()

        # graphing results
        if graph:
            colours = ["#FFB000", "#FE6100", "#DC267F", "#785EF0", "#648FFF"]

            fig, ax1 = plt.subplots()
            ax2 = ax1.twinx()
            ax1.plot(param_list, measure_list, linestyle="", marker="+",
                     markersize=5, color=colours[0])
            ax2.plot(param_list, runtime_list, linestyle="", marker="+",
                     markersize=5, color=colours[2])
            ax1.set_ylabel(r"growth rate $\gamma$", color=colours[0])
            ax2.set_ylabel(r"runtime (s)", color=colours[2])
            ax1.tick_params(axis="y", labelcolor=colours[0])
            ax2.tick_params(axis="y", labelcolor=colours[2])
            ax1.set_xlabel("ntheta")
            fig.tight_layout()
            plt.show(block=True)
        if self.tolerance == 0:
            plt.plot(param_list, measure_list, linestyle="", marker="+", markersize=5)
            plt.ylabel(r"growth rate $\gamma$")
            plt.xlabel("ntheta")
            plt.show(block=True)


class scan:

    def __init__(
            self,
            pyro,  # pyro object
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
            param_name="",  # parameter being varied
            initial=0,  # parameter initial value
            final=1,  # parameter final value
            increment=1,  # parameter increment
            measure_names=[],  # quantities being measured
            save_results=True,  # whether results are saved
            graph=False  # whether results are displayed in a graph
    ):
        param_initial_value = initial
        param_final_value = final
        param_initial_increment = increment
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
                param_value += param_increment

                if param_value >= param_final_value:
                    end = True

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

                param_list.append(param_value)  # records current parameter value

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

            if graph:  # plots results on a graph
                i = 0
                while i < len(measure_list):

                    if len(measure_names) > 50:
                        markersize = 1
                        marker = ""
                        linestyle = "-"
                    elif len(measure_names) > 35:
                        markersize = 4
                        marker = "+"
                        linestyle = ""
                    elif len(measure_names) > 20:
                        markersize = 8
                        marker = "+"
                        linestyle = ""
                    else:
                        markersize = 10
                        marker = "+"
                        linestyle = ""
                    plt.plot(param_list, measure_list[i],
                             linestyle=linestyle,
                             marker=marker, markersize=markersize)
                    if measure_names[i] == "gamma":
                        plt.ylabel(r"$\gamma$")
                    if param_name == "beta":
                        plt.xlabel("$\\beta$")
                    plt.show(block=True)
                    i += 1


class data:

    def __init__(
            self,
            param,
            measure,
    ):
        self.param_name = param
        self.param_data = []
        self.measure_names = measure
        self.measure_data = []
        self.titles=[]

    def load(
            self,
            path,
            title
    ):
        self.param_data.append([])
        self.measure_data.append([])
        self.titles.append(title)


        i = 1
        while i <= len(self.measure_names):
            self.measure_data[len(self.measure_data) - 1].append([])
            i += 1

        print(self.measure_data)

        output_files = glob.glob(f"{path}*.out.nc")

        # loops over every output file, loading data
        i = 0
        while i < len(output_files):
            ds = xarray.open_dataset(output_files[i])

            # records parameter value for the gs2 run
            if self.param_name == "beta":
                self.param_data[len(self.measure_data) - 1].append(float(ds.beta))

            # for each measurement, saves the value to a list
            k = 0
            while k < len(self.measure_names):
                if self.measure_names[k] == "gamma":
                    measure_value = ds.omega.isel(ri=1, t=-1).values
                else:
                    print("Error: invalid measure_name")
                    return
                self.measure_data[len(self.measure_data) - 1][k].append(measure_value[0][0])
                k += 1
            i = i + 1

        temp_measure_data = [[]]
        i = 1
        while i < len(self.measure_names):
            temp_measure_data.append([])
            i += 1

        # sorts data
        i = 0
        while i < len(self.measure_names):
            temp_measure_data[i] = list(self.measure_data[len(self.measure_data) - 1][i][j]
                                        for j in np.argsort(
                                        self.param_data[len(self.param_data) - 1]))
            print(temp_measure_data)
            self.measure_data[len(self.measure_data) - 1][i] = temp_measure_data[i]
            i += 1
        self.param_data = list(np.sort(self.param_data))

    def append(
            self,
            path
    ):
        directory = path

    def graph(
            self,
            markersize=5,
            marker="+",
            linestyle=""
    ):
        colours = ["#FFB000", "#FE6100", "#DC267F", "#785EF0", "#648FFF"]
        i = 0
        j = 0
        while i < len(self.measure_names):

            while j < len(self.measure_data):
                if len(self.measure_data) == 1:
                    plt.plot(self.param_data[j], self.measure_data[j][i],
                         linestyle=linestyle, color=colours[j],
                         marker=marker, markersize=markersize,
                         label=f"{self.titles[j]}"
                         )
                else:
                    plt.plot(self.param_data[j], self.measure_data[j][i],
                             linestyle=linestyle, color=colours[j],
                             marker=marker, markersize=markersize
                             )
                j += 1
            if self.measure_names[i] == "gamma":
                plt.ylabel(r"$\gamma$")
            if self.param_name == "beta":
                plt.xlabel("$\\beta$")
            if len(self.measure_data) != 1:
                plt.legend(loc="upper left")
            plt.show(block=True)
            i += 1
