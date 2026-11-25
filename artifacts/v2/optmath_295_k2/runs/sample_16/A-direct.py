import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    arc_capacity = params["arc_capacity"]

    n_origins = len(supply)
    n_dests = len(demand)

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, n_origins - 1)
    model.dests = pyo.RangeSet(0, n_dests - 1)

    def cap_rule(model, i, j):
        return (0, arc_capacity[i][j])

    model.flow = pyo.Var(model.origins, model.dests, bounds=cap_rule)

    def obj_rule(model):
        return sum(cost[i][j] * model.flow[i, j]
                   for i in model.origins for j in model.dests)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(model, i):
        return sum(model.flow[i, j] for j in model.dests) == supply[i]

    model.supply_con = pyo.Constraint(model.origins, rule=supply_rule)

    def demand_rule(model, j):
        return sum(model.flow[i, j] for i in model.origins) == demand[j]

    model.demand_con = pyo.Constraint(model.dests, rule=demand_rule)

    try:
        Highs().solve(model)
    except Exception as exc:
        return {"objective": None, "status": "solver failed: " + str(exc)}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "no feasible solution"}

    return {"objective": obj_val, "status": "optimal"}