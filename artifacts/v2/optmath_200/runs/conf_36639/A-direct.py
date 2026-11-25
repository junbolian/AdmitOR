import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_hubs = int(params["num_hubs"])
    hubs = list(range(num_hubs))
    source = 0
    sink = num_hubs - 1

    arcs = [(i, j) for i in hubs for j in hubs if i != j]

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.HUBS = pyo.Set(initialize=hubs)

    def _cost_init(mdl, i, j):
        return params["cost_{}_{}".format(i, j)]

    model.cost = pyo.Param(model.ARCS, initialize=_cost_init)

    model.flow = pyo.Var(model.ARCS, domain=pyo.Binary)

    def _obj_rule(mdl):
        return sum(mdl.cost[i, j] * mdl.flow[i, j] for (i, j) in mdl.ARCS)

    model.total_cost = pyo.Objective(rule=_obj_rule, sense=pyo.minimize)

    supply = params["supply_hub0"]
    demand = params["demand_hub10"]

    def _balance_rule(mdl, k):
        outflow = sum(mdl.flow[k, j] for j in hubs if j != k)
        inflow = sum(mdl.flow[i, k] for i in hubs if i != k)
        if k == source:
            return outflow - inflow == supply
        elif k == sink:
            return inflow - outflow == demand
        else:
            return outflow - inflow == 0

    model.balance = pyo.Constraint(model.HUBS, rule=_balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}