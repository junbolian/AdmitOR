import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]
    pair_capacity = params["pair_capacity"]

    n_orig = len(supply)
    n_dest = len(demand)

    model = pyo.ConcreteModel()
    model.orig = pyo.RangeSet(0, n_orig - 1)
    model.dest = pyo.RangeSet(0, n_dest - 1)

    model.x = pyo.Var(model.orig, model.dest, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            transport_cost[i][j] * m.x[i, j]
            for i in m.orig for j in m.dest
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.dest) == supply[i]
    model.supply_con = pyo.Constraint(model.orig, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.orig) == demand[j]
    model.demand_con = pyo.Constraint(model.dest, rule=demand_rule)

    def cap_rule(m, i, j):
        return m.x[i, j] <= pair_capacity[i][j]
    model.cap_con = pyo.Constraint(model.orig, model.dest, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}