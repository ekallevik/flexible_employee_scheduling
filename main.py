from model.model import create_model, setup_model, run_model


def main():
    model = create_model()
    setup_model(model, find_optimal_solution=False)
    run_model(model)


main()
