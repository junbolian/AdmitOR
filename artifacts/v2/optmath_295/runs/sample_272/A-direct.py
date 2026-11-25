import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    areas = list(range(9))
    towers = list(range(9))

    coverage = {
        0: [2, 4, 5, 6, 7],
        1: [0, 1, 6, 8],
        2: [1, 6, 8],
        3: [1, 2, 6, 7],
        4: [0, 2, 3, 6, 7, 8],
        5: [0, 1, 2, 6, 7],
        6: [0, 1, 2, 4],
        7: [1, 2, 4, 5, 6],
        8: [0, 1, 3, 4, 5, 8],
    }

    model = pyo.ConcreteModel()

    model.x = pyo.Var(towers, domain=pyo.Binary)
    model.y = pyo.Var(areas, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(population[i] * model.y[i] for i in areas),
        sense=pyo.maximize,
    )

    model.budget_con = pyo.Constraint(
        expr=sum(tower_cost[j] * model.x[j] for j in towers) <= budget
    )

    model.coverage_con = pyo.Constraint(
        areas,
        rule=lambda m, i: m.y[i] <= sum(m.x[j] for j in coverage[i]),
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}