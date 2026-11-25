import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    cap = params["cap"]

    n_src = len(supply)
    n_dst = len(demand)
    srcs = list(range(n_src))
    dsts = list(range(n_dst))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(srcs, dsts, domain=pyo.NonNegativeReals, bounds=lambda m, i, j: (0, cap[i][j]))

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in dsts) <= supply[i]
    model.supply_con = pyo.Constraint(srcs, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in srcs) >= demand[j]
    model.demand_con = pyo.Constraint(dsts, rule=demand_rule)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in srcs for j in dsts)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}