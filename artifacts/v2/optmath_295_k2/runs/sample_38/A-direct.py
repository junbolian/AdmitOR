import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_origin = len(supply)
    n_dest = len(demand)
    origins = list(range(n_origin))
    dests = list(range(n_dest))

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=[(i, j) for i in origins for j in dests])

    model.x = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(model, i, j):
        return model.x[i, j] <= capacity[i][j]

    model.capacity_con = pyo.Constraint(model.arcs, rule=capacity_rule)

    def supply_rule(model, i):
        return sum(model.x[i, j] for j in dests) == supply[i]

    model.supply_con = pyo.Constraint(origins, rule=supply_rule)

    def demand_rule(model, j):
        return sum(model.x[i, j] for i in origins) == demand[j]

    model.demand_con = pyo.Constraint(dests, rule=demand_rule)

    def obj_rule(model):
        return sum(cost[i][j] * model.x[i, j] for (i, j) in model.arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}