import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_orig = len(supply)
    n_dest = len(demand)

    origins = list(range(n_orig))
    destinations = list(range(n_dest))
    arcs = [(i, j) for i in origins for j in destinations]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.NonNegativeReals)

    def cost_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in destinations) == supply[i]

    model.supply_con = pyo.Constraint(origins, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in origins) == demand[j]

    model.demand_con = pyo.Constraint(destinations, rule=demand_rule)

    def cap_rule(mdl, i, j):
        return mdl.x[i, j] <= capacity[i][j]

    model.cap_con = pyo.Constraint(arcs, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}