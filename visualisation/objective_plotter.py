from visualisation.abstract_plotter import AbstractPlotter


class ObjectivePlotter(AbstractPlotter):

    def __init__(self, title):
        super().__init__(title)

        fig = self.plt.figure()

        self.plt.yscale('symlog')
        self.plt.grid(True)

    def plot_data(self, data):

        # todo: add time as x-value?
        # todo: change to line plotter?

        candidate_plot, = self.plt.plot(data["candidate"],
                                        label="candidate",
                                        color="lightcoral",
                                        linestyle=":")

        current_plot, = self.plt.plot(data["current"],
                                      label="current",
                                      color="darkviolet",
                                      linestyle="-.")

        best_plot, = self.plt.plot(data["best"], label="best", color="royalblue", linestyle="--")

        best_legal_plot, = self.plt.plot(data["best_legal"], label="best legal", color="forestgreen",
                                         linestyle="-")

        self.plt.legend(handles=[candidate_plot, current_plot, best_plot, best_legal_plot],
                        loc='lower left')

        self.show()
