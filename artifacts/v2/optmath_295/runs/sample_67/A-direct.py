import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    hub_costs = params["hub_costs"]
    n_hubs = 15
    route_servers = [
        [2, 3, 4, 7, 11, 13],
        [10, 12, 15],
        [1, 5, 6, 8, 11, 12, 13, 14],
        [2, 3, 4, 6, 7, 10, 12, 14],
        [1, 2, 3, 10, 13],
        [1, 2, 3, 6, 8, 10, 11, 12, 14],
        [3, 4, 5, 7, 8, 10, 11, 13, 14],
        [1, 2, 3, 7, 9, 12, 13],
        [1, 4, 7, 10, 12, 13, 14],
        [1, 3, 4, 5, 7, 10, 11, 13, 14, 15],
        [1, 4, 7, 9, 13, 14],
        [3, 4, 6, 8, 10, 11, 12, 13, 14, 15],
        [1, 2, 4, 5, 7, 11, 13, 14],
        [1, 4, 5, 6, 9, 12, 14, 15],
        [2, 6, 7, 12, 13, 14],
        [1, 4, 8, 11, 12, 14, 15],
    ]

    model = pyo.ConcreteModel()
    model.H = pyo.RangeSet(1, n_hubs)
    model.R = pyo.RangeSet(1, len(route_servers))
    model.x = pyo.Var(model.H, domain=pyo.Binary)

    model.cost = pyo.Objective(
        expr=sum(hub_costs[j - 1] * model.x[j] for j in model.H),
        sense=pyo.minimize,
    )

    model.route_cov = pyo.Constraint(
        model.R,
        rule=lambda model, i: sum(model.x[j] for j in route_servers[i - 1]) >= 1,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}