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

    model.ORIG = pyo.RangeSet(0, n_orig - 1)
    model.DEST = pyo.RangeSet(0, n_dest - 1)

    model.x = pyo.Var(model.ORIG, model.DEST, domain=pyo.NonNegativeReals)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.DEST) <= supply[i]

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.ORIG) == demand[j]

    def capacity_rule(m, i, j):
        return m.x[i, j] <= capacity[i][j]

    model.supply_con = pyo.Constraint(model.ORIG, rule=supply_rule)
    model.demand_con = pyo.Constraint(model.DEST, rule=demand_rule)
    model.capacity_con = pyo.Constraint(model.ORIG, model.DEST, rule=capacity_rule)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.ORIG for j in m.DEST)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}