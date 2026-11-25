import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    populations = params["populations"]
    tower_costs = params["tower_costs"]
    budget = params["budget"]
    num_regions = int(params["num_regions"])
    num_towers = int(params["num_towers"])

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

    regions = list(range(num_regions))
    towers = list(range(num_towers))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(towers, domain=pyo.Binary)
    model.y = pyo.Var(regions, domain=pyo.Binary)

    model.budget_con = pyo.Constraint(
        expr=sum(tower_costs[t] * model.x[t] for t in towers) <= budget
    )

    model.coverage_con = pyo.Constraint(
        regions,
        rule=lambda m, r: sum(m.x[t] for t in coverage[r] if t < num_towers) >= m.y[r]
    )

    model.obj = pyo.Objective(
        expr=sum(populations[r] * model.y[r] for r in regions),
        sense=pyo.maximize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}