import numpy as np

from visualisation.abstract_plotter import AbstractPlotter


class HeatmapPlotter(AbstractPlotter):

    def __init__(self, title):
        super().__init__(title)

        self.fig, self.ax = self.plt.subplots()
        self.im = None

    def plot_data(self, data):

        values, x_labels, y_labels = self.format_data(data)

        if not self.im:
            self.set_formatting(x_labels, y_labels)

        self.im = self.ax.imshow(values)
        self.fig.tight_layout()

        super().show()

    @staticmethod
    def format_data(data):
        """
        Formats the data into an appropriate format:
            - x_labels is the range of the variables
            - y_labels is the name of each variable
            - values is a 2D containing a list of values for each variable
        """

        x_labels = None
        y_labels = []
        values = []

        for key, value in data.items():
            y_labels.append(key)
            values.append(value)

            if not x_labels:
                x_labels = range(len(value))

        return values, x_labels, y_labels

    def set_formatting(self, x_labels, y_labels):

        # Show all ticks
        self.ax.set_xticks(np.arange(len(x_labels)))
        self.ax.set_yticks(np.arange(len(y_labels)))

        # Label ticks with the respective list entries
        self.ax.set_xticklabels(x_labels)
        self.ax.set_yticklabels(y_labels)
