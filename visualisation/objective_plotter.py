from visualisation.abstract_plotter import AbstractPlotter


class ObjectivePlotter(AbstractPlotter):

    def __init__(self, title, log_name):
        super().__init__(title, log_name)

        self.fig = self.plt.figure()
        self.fig.suptitle(self.log_name, fontsize=14, fontweight='bold')

        self.plt.yscale('linear')
        self.plt.grid(True)

    def plot_data(self, data):

        # todo: add time as x-value?

        handles = []
        linestyle = [":", "-.", "--", "-"]
        colors = ["lightcoral", "darkviolet", "royalblue", "forestgreen", "orange", "slategray",
                  "darkred", "palegreen", "chocalate"]

        for count, (key, value) in enumerate(data.items()):
            color_index = count % len(colors)
            line_index = count % len(linestyle)
            line, = self.plt.plot(value,
                                  label=key,
                                  color=colors[color_index],
                                  linestyle=linestyle[line_index])
            handles.append(line)

        self.plt.legend(handles=handles,
                        loc='lower center', bbox_to_anchor=(0.5, -0.15),
                        fancybox=True, shadow=True, ncol=3)

        self.show()
