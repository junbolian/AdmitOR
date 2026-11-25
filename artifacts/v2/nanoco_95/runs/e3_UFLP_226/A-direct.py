import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["location_investment_cost"]
    dist = params["distance_matrix"]

    n_demand = len(dist)
    n_sites = len(cost)

    model = pyo.ConcreteModel()

    model.DEMAND = pyo.RangeSet(0, n_demand - 1)
    model.SITES = pyo.RangeSet(0, n_sites - 1)

    model.y = pyo.Var(model.SITES, domain=pyo.Binary)
    model.x = pyo.Var(model.DEMAND, model.SITES, domain=pyo.Binary)

    def obj_rule(mdl):
        invest = sum(cost[j] * mdl.y[j] for j in mdl.SITES)
        travel = sum(dist[i][j] * mdl.x[i, j] for i in mdl.DEMAND for j in mdl.SITES)
        return invest + travel

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.assign_once = pyo.Constraint(
        model.DEMAND,
        rule=lambda mdl, i: sum(mdl.x[i, j] for j in mdl.SITES) == 1,
    )

    model.link = pyo.Constraint(
        model.DEMAND,
        model.SITES,
        rule=lambda mdl, i, j: mdl.x[i, j] <= mdl.y[j],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}