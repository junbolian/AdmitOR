import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    n_regions = len(population)
    n_towers = len(tower_cost)

    coverage = [
        [1, 2, 4, 5, 6],
        [0, 1, 3, 6],
        [0, 1, 2, 4],
        [0, 1, 2, 3, 5],
        [0, 1, 2, 3, 5],
        [0, 1, 2, 6],
        [3],
        [3, 4, 6],
        [0, 2],
        [1, 3, 4, 5],
        [1, 3, 5, 6],
    ]

    model = pyo.ConcreteModel()

    model.TOWERS = pyo.RangeSet(0, n_towers - 1)
    model.REGIONS = pyo.RangeSet(0, n_regions - 1)

    model.build = pyo.Var(model.TOWERS, domain=pyo.Binary)
    model.covered = pyo.Var(model.REGIONS, domain=pyo.Binary)

    model.budget_con = pyo.Constraint(
        expr=sum(tower_cost[t] * model.build[t] for t in model.TOWERS) <= budget
    )

    def coverage_rule(model, r):
        return model.covered[r] <= sum(model.build[t] for t in coverage[r])

    model.coverage_con = pyo.Constraint(model.REGIONS, rule=coverage_rule)

    model.obj = pyo.Objective(
        expr=sum(population[r] * model.covered[r] for r in model.REGIONS),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}