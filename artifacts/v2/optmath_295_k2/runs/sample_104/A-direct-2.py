import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    regions = list(range(10))
    towers = list(range(8))

    coverage = {
        0: [0, 3, 5, 7],
        1: [2, 6],
        2: [1, 3, 5],
        3: [0, 2, 5, 6, 7],
        4: [4, 6],
        5: [0, 1, 2, 5, 6],
        6: [1, 3, 4, 6],
        7: [0, 1, 6],
        8: [4, 5, 6, 7],
        9: [3, 4, 5, 6],
    }

    model = pyo.ConcreteModel()

    model.TOWERS = pyo.Set(initialize=towers)
    model.REGIONS = pyo.Set(initialize=regions)

    model.build = pyo.Var(model.TOWERS, domain=pyo.Binary)
    model.covered = pyo.Var(model.REGIONS, domain=pyo.Binary)

    model.budget_con = pyo.Constraint(
        expr=sum(tower_cost[t] * model.build[t] for t in model.TOWERS) <= budget
    )

    def coverage_rule(m, r):
        return m.covered[r] <= sum(m.build[t] for t in coverage[r])

    model.coverage_con = pyo.Constraint(model.REGIONS, rule=coverage_rule)

    def serve_rule(m, r):
        return sum(m.build[t] for t in coverage[r]) >= 1

    model.serve_con = pyo.Constraint(model.REGIONS, rule=serve_rule)

    model.obj = pyo.Objective(
        expr=sum(population[r] * model.covered[r] for r in model.REGIONS),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}