import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_orig = len(supply)
    n_dest = len(demand)

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, n_orig - 1)
    model.dests = pyo.RangeSet(0, n_dest - 1)

    model.flow = pyo.Var(model.origins, model.dests, within=pyo.NonNegativeReals)

    def flow_upper(model, i, j):
        return model.flow[i, j] <= capacity[i][j]
    model.capacity_rule = pyo.Constraint(model.origins, model.dests, rule=flow_upper)

    def supply_rule(model, i):
        return sum(model.flow[i, j] for j in model.dests) == supply[i]
    model.supply_con = pyo.Constraint(model.origins, rule=supply_rule)

    def demand_rule(model, j):
        return sum(model.flow[i, j] for i in model.origins) == demand[j]
    model.demand_con = pyo.Constraint(model.dests, rule=demand_rule)

    def obj_rule(model):
        return sum(cost[i][j] * model.flow[i, j]
                   for i in model.origins for j in model.dests)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or solve failed"}