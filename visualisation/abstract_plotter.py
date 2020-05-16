
from matplotlib import pyplot as plt


class AbstractPlotter:

    def __init__(self, title):

        plt.style.use('seaborn-pastel')
        self.plt = plt

        self.plt.ion()

        self.title = title

    def plot_data(self, data):

        raise NotImplementedError

    def show(self):
        self.plt.title(self.title)
        self.plt.show()
        self.plt.pause(0.0001)
