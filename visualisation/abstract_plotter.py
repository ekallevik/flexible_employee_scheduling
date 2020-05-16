
from matplotlib import pyplot as plt


class AbstractPlotter:

    def __init__(self):

        plt.style.use('seaborn-pastel')
        self.plt = plt

    def plot_data(self, data):
        raise NotImplementedError
