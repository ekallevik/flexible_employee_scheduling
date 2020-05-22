
from matplotlib import pyplot as plt


class AbstractPlotter:

    def __init__(self, title, log_name):

        plt.style.use('seaborn-pastel')
        self.plt = plt

        self.plt.ion()

        self.title = title
        self.log_name = log_name

    def plot_data(self, data):

        raise NotImplementedError

    def show(self):
        self.plt.title(self.title)
        self.plt.show()
        self.plt.pause(0.0001)
