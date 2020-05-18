import numpy as np

from visualisation.abstract_plotter import AbstractPlotter


class BarchartPlotter(AbstractPlotter):

    def __init__(self, title):

        super().__init__(title)

        self.labels = None
        self.label_locations = None
        self.width = None
        self.no_of_groupings = None
        self.location_offset = None

        self.fig, self.ax = self.plt.subplots()

    def set_labels(self, data):

        no_of_labels = len(data)

        self.labels = [i for i in range(no_of_labels)]
        self.label_locations = np.arange(no_of_labels)  # the label locations
        self.width = 0.25  # the width of the bars

    def plot_data(self, data):

        self.plt.cla()

        if not self.labels:
            self.set_labels(data["above_demand"])
            self.ax.set_ylabel('Scores')
            self.ax.set_title('Scores by group and gender')
            self.ax.set_xticks(self.label_locations)

        above_maximum = data["above_demand"]
        below_minimum = data["below_demand"]
        contracted_hours = data["contracted_hours"]

        rects1 = self.ax.bar(self.label_locations - self.width, above_maximum, self.width,
                             label='above_maximum')
        rects2 = self.ax.bar(self.label_locations, below_minimum, self.width,
                             label='below_minimum')
        rects3 = self.ax.bar(self.label_locations + self.width, contracted_hours, self.width,
                             label='contracted_hours')

        self.ax.set_xticklabels(self.labels)
        self.ax.legend()

        self.autolabel(rects1, self.ax)
        self.autolabel(rects2, self.ax)
        self.autolabel(rects3, self.ax)

        self.fig.tight_layout()

        self.show()


    def autolabel(self, rects, ax):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = rect.get_height()
            if height:
                ax.annotate('{}'.format(height),
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom')




