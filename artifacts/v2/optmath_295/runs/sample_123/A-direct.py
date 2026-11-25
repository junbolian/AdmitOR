import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    populations = params["populations"]
    tower_costs = params["tower_costs"]
    budget = params["budget"]

    coverage = [
        [0, 3, 5, 6],
        [2, 3, 4, 6],
        [0, 1, 4, 5, 6],
        [0, 3, 4],
        [0, 3, 4],
        [1, 2, 3],
        [1, 2, 3, 4],
        [1, 2, 3, 4, 5, 6],
        [0, 1, 2, 4, 5],
        [1, 4, 6],
    ]

    n_regions = 10
    n_towers = 7

    model = pyo.ConcreteModel()

    model.TOWERS = pyo.RangeSet(0, n_towers - 1)
    model.REGIONS = pyo.RangeSet(0, n_regions - 1)

    model.build = pyo.Var(model.TOWERS, domain=pyo.Binary)
    model.covered = pyo.Var(model.REGIONS, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(populations[r] * model.covered[r] for r in model.REGIONS),
        sense=pyo.maximize,
    )

    model.budget_con = pyo.Constraint(
        expr=sum(tower_costs[t] * model.build[t] for t in model.TOWERS) <= budget
    )

    def coverage_rule(mdl, r):
        return mdl.covered[r] <= sum(mdl.build[t] for t in coverage[r])

    model.coverage_con = pyo.Constraint(model.REGIONS, rule=coverage_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}