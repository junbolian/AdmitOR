import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    regions = list(range(11))
    towers = list(range(7))

    coverage = {
        0: [1, 2, 4, 5, 6],
        1: [0, 1, 3, 6],
        2: [0, 1, 2, 4],
        3: [0, 1, 2, 3, 5],
        4: [0, 1, 2, 3, 5],
        5: [0, 1, 2, 6],
        6: [3],
        7: [3, 4, 6],
        8: [0, 2],
        9: [1, 3, 4, 5],
        10: [1, 3, 5, 6],
    }

    model = pyo.ConcreteModel()
    model.T = pyo.Set(initialize=towers)
    model.R = pyo.Set(initialize=regions)

    model.build = pyo.Var(model.T, domain=pyo.Binary)
    model.cov = pyo.Var(model.R, domain=pyo.Binary)

    model.cov_con = pyo.Constraint(
        model.R,
        rule=lambda m, r: m.cov[r] <= sum(m.build[t] for t in coverage[r]),
    )

    model.budget_con = pyo.Constraint(
        expr=sum(tower_cost[t] * model.build[t] for t in towers) <= budget
    )

    model.obj = pyo.Objective(
        expr=sum(population[r] * model.cov[r] for r in regions),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}