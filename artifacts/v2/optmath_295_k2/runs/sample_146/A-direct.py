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

    model.orig = pyo.RangeSet(0, n_orig - 1)
    model.dest = pyo.RangeSet(0, n_dest - 1)

    def flow_bounds(m, i, j):
        return (0, capacity[i][j])

    model.flow = pyo.Var(model.orig, model.dest, bounds=flow_bounds)

    def obj_rule(m):
        return sum(cost[i][j] * m.flow[i, j] for i in m.orig for j in m.dest)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.flow[i, j] for j in m.dest) == supply[i]

    model.supply_con = pyo.Constraint(model.orig, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.flow[i, j] for i in m.orig) == demand[j]

    model.demand_con = pyo.Constraint(model.dest, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}