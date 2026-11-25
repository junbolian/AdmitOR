import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    areas = list(range(9))
    towers = list(range(9))

    coverage_map = {
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

    model.build = pyo.Var(towers, domain=pyo.Binary)
    model.cover = pyo.Var(areas, domain=pyo.Binary)

    model.budget_con = pyo.Constraint(
        expr=sum(tower_cost[t] * model.build[t] for t in towers) <= budget
    )

    def coverage_rule(m, a):
        return m.cover[a] <= sum(m.build[t] for t in coverage_map[a])

    model.coverage_con = pyo.Constraint(areas, rule=coverage_rule)

    model.obj = pyo.Objective(
        expr=sum(population[a] * model.cover[a] for a in areas),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}