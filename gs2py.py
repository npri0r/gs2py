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
            tolerance=0.01,
            gs2_directory="~/gs2/bin/gs2",
            max=100  # max number of simulations before force quitting
    ):
        # stores the pyro object
        self.pyro = pyro
        # % difference between outputs to be considered 'converged'
        self.tolerance = tolerance
        # gs2 directory
        self.gs2_directory = gs2_directory
        # max number of simulations
        self.max = max

    def run(
            self,
            param_name,  # parameter being changed
            measure_name,  # quantity being measured
            param_initial_value,  # parameter initial value
            param_initial_increment,  # parameter initial variance increment
            save_results=True,  # whether results are saved
            graph=False  # whether results are displayed in a graph
    ):
        input_file = self.pyro.gk_file


        param_list = []  # stores parameter values for each run
        measure_list = []  # stores calculated values for each run
        param_value = param_initial_value - param_initial_increment  # sets initial parameter
        runtime_list = []  # stores runtime_list

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


                print(f"Ran gs2 for {param_name} = {param_value}")
                print(f"{measure_name} = {measure_value[0][0]}")


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
                     markersize=10, color=colours[0])
            ax2.plot(param_list, runtime_list, linestyle="", marker="+",
                     markersize=10, color=colours[2])
            ax1.set_ylabel(r"growth rate $\gamma$", color=colours[0])
            ax2.set_ylabel(r"runtime (s)", color=colours[2])
            ax1.tick_params(axis="y", labelcolor=colours[0])
            ax2.tick_params(axis="y", labelcolor=colours[2])
            ax1.set_xlabel("ntheta")
            fig.tight_layout()
            plt.show(block=True)


class scan:

    def __init__(
            self,
            pyro,  # pyro object
            gs2_directory="~/gs2/bin/gs2",
    ):
        # stores the pyro object
        self.pyro = pyro
        # gs2 directory
        self.gs2_directory = gs2_directory

    def run(
            self,
            param_name,  # parameter being varied
            measure_names,  # quantities being measured
            initial,  # parameter initial value
            final,  # parameter final value
            increment,  # parameter increment
            save_results=True,  # whether results are saved
            folder_name="",
            new_folder=True,
            smart=False,
            cap=4,      # when smart, limits recursion
            smart_data=[0, 0, 0, 0]     # data used in smart scans. Do not manually change this.
    ):
        param_initial_value = initial
        param_final_value = final
        param_initial_increment = increment
        input_file = self.pyro.gk_file
        scan_data = data(param_name, measure_names)

        if folder_name == "":
            folder_name = f"gs2py_{param_name}_scan_"

        param_value = param_initial_value - param_initial_increment  # sets initial parameter
        param_increment = param_initial_increment  # sets initial increment

        # file management
        with open(input_file, "r") as file:  # opens input file

            if new_folder:
                # creates folder to contain outputs
                j = 1
                while j > 0:  # creates a uniquely numbered directory
                    if os.path.exists(f"{str(folder_name) + str(j)}"):
                        j += 1
                    else:
                        j = -j
                j = -j
                folder_name = str(folder_name) + str(j)
                subprocess.run(f"mkdir {folder_name}", shell=True)

            scan_data.new_load(f"{folder_name}")

            # begins loop of gs2 runs
            end = False
            while not end:
                param_value += param_increment

                if param_value >= param_final_value:
                    end = True

                # create new gs2 input file with altered parameter
                with open(f"{folder_name}//{param_value}.in", "w") as newfile:
                    file.seek(0)
                    for line in file:
                        match = re.search(f"{param_name} = ", line)
                        if match:
                            newline = f"  {param_name} = {param_value}\n"
                            newfile.write(line.replace(line, newline))
                        else:
                            newfile.write(line)
                newfile.close()

                # runs gs2
                subprocess.run("mpirun -np 4 "
                               f"~/gs2/bin/gs2 {folder_name}/{param_value}.in",
                               shell=True)
                print(f"Ran gs2 for {param_name} = {param_value}")
                # data processing
                scan_data.load(f"{folder_name}/{param_value}.out.nc")

            if smart:
                print(f"Smart scan level: {smart_data[0]}")
                scan_data = self.smart_scan(scan_data, cap, smart_data, folder_name)

            # deleting temporary files
            if not save_results:
                subprocess.run(f"rm -r {folder_name}", shell=True)
            file.close()

            return scan_data

    def smart_scan(
            self,
            scan_data,
            cap,  # limits number of recursions
            smart_data,
            folder_name
    ):
        scan_data.sort()
        level = smart_data[0]
        indx = smart_data[3]
        diff = []
        i = 1
        while i <= len(scan_data.measure_data[0][0])-1:
            diff.append(scan_data.measure_data[0][0][i] - scan_data.measure_data[0][0][i - 1])
            i += 1

        if level == 0:
            dev = np.std(diff)
            mean = np.mean(diff)
        else:
            dev = smart_data[1]
            mean = smart_data[2]
        if level < cap:
            level += 1
            i = 0
            while i <= len(diff)-1:
                if diff[i] > (dev + mean)/2:
                    initial = scan_data.param_data[0][i]
                    final = scan_data.param_data[0][i+1]
                    increment = (final - initial) / 2
                    print(f"Running new scan between {initial} and {final}")
                    new_data = self.run(scan_data.param_name, scan_data.measure_names,
                                        initial, final, increment,
                                        folder_name=folder_name, new_folder=False,
                                        smart=True, cap=cap,
                                        smart_data=[level, dev, mean, indx])
                    j = 0
                    while j <= len(scan_data.measure_names)-1:
                        scan_data.measure_data[0][j] = scan_data.measure_data[0][j] + new_data.measure_data[0][j]
                        j += 1
                    scan_data.param_data[0] = scan_data.param_data[0] + new_data.param_data[0]
                    scan_data.sort()
                i += 1
        return scan_data


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
        self.titles = []

    def __str__(
                 self,
    ):
        print("Dataset titles:")
        print(self.titles)
        print(f"{self.param_name} data:")
        print(self.param_data)
        print(f"{self.measure_names} data:")
        print(self.measure_data)

    def mult_load(
            self,
            path,
            title=""
    ):
        self.new_load(title)

        output_files = glob.glob(f"{path}*.out.nc")

        # loops over every output file, loading data
        i = 0
        while i < len(output_files):
            self.load(output_files[i])
            i = i + 1

    def sort(
            self
    ):

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
            self.measure_data[len(self.measure_data) - 1][i] = temp_measure_data[i]
            i += 1
        self.param_data[len(self.param_data)-1].sort()

    def load(
            self,
            path,
    ):
        ds = xarray.open_dataset(path)

        # records parameter value for the gs2 run
        if self.param_name == "beta":
            self.param_data[len(self.measure_data) - 1].append(float(ds.beta))

        # for each measurement, saves the value to a list
        k = 0
        while k < len(self.measure_names):
            if self.measure_names[k] == "gamma":
                measure_value = ds.omega.isel(ri=1, t=-1).values
            elif self.measure_names[k] == "omega":
                measure_value = ds.omega.isel(ri=0, t=-1).values
            elif self.measure_names[k] == "runtime":
                timepath = path.replace("out.nc", "timing_stats")
                with open(timepath, "r") as newfile:
                    newfile.seek(0)
                    for line in newfile:
                        match = re.search("Total", line)
                        if match:
                            times = re.split("\\s+", line)
                            measure_value = times[3]
                newfile.close()
            else:
                print("Error: invalid measure_name")
                return
            self.measure_data[len(self.measure_data) - 1][k].append(measure_value[0][0])
            k += 1

    def new_load(
            self,
            title="",
    ):

        self.param_data.append([])
        self.measure_data.append([])
        self.titles.append(title)

        i = 1
        while i <= len(self.measure_names):
            self.measure_data[len(self.measure_data) - 1].append([])
            i += 1

    def graph(
            self,
            markersize=5,
            marker="+",
            linestyle=""
    ):
        colours = ["#FFB000", "#FE6100", "#DC267F", "#785EF0", "#648FFF"]
        i = 0

        self.sort()

        while i < len(self.measure_names):
            j = 0
            while j < len(self.measure_data):
                if len(self.measure_data) == 1:
                    plt.plot(self.param_data[j], self.measure_data[j][i],
                             linestyle=linestyle, color=colours[j],
                             marker=marker, markersize=markersize
                             )
                else:
                    plt.plot(self.param_data[j], self.measure_data[j][i],
                             linestyle=linestyle, color=colours[j],
                             marker=marker, markersize=markersize,
                             label=f"{self.titles[j]}"
                             )
                j += 1
            if self.measure_names[i] == "gamma":
                plt.ylabel(r"$\gamma$")
            elif self.measure_names[i] == "omega":
                plt.ylabel(r"$\omega$")
            if self.param_name == "beta":
                plt.xlabel("$\\beta$")
            if len(self.measure_data) != 1:
                plt.legend(loc="upper left")
            plt.show(block=True)
            i += 1
