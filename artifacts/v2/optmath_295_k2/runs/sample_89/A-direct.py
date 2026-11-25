import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n_orig = len(supply)
    n_dest = len(demand)

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, n_orig - 1)
    model.destinations = pyo.RangeSet(0, n_dest - 1)

    model.transport = pyo.Var(
        model.origins, model.destinations, domain=pyo.NonNegativeReals
    )

    def total_cost_rule(mdl):
        return sum(
            cost[i][j] * mdl.transport[i, j]
            for i in range(n_orig)
            for j in range(n_dest)
        )

    model.total_cost = pyo.Objective(rule=total_cost_rule, sense=pyo.minimize)

    def supply_rule(mdl, i):
        return sum(mdl.transport[i, j] for j in range(n_dest)) <= supply[i]

    model.supply_con = pyo.Constraint(model.origins, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.transport[i, j] for i in range(n_orig)) == demand[j]

    model.demand_con = pyo.Constraint(model.destinations, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}