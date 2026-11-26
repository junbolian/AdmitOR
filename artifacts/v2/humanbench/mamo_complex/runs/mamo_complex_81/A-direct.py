import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_centers = 6
    n_stores = 4

    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(0, n_centers - 1)
    model.stores = pyo.RangeSet(0, n_stores - 1)
    model.arcs = pyo.Set(initialize=[(i, j) for i in range(n_centers) for j in range(n_stores)])

    model.open = pyo.Var(model.centers, domain=pyo.Binary)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def demand_rule(md, j):
        return sum(md.flow[i, j] for i in range(n_centers)) == demand[j]

    model.demand_con = pyo.Constraint(model.stores, rule=demand_rule)

    def cap_rule(md, i):
        return sum(md.flow[i, j] for j in range(n_stores)) <= capacity[i] * md.open[i]

    model.cap_con = pyo.Constraint(model.centers, rule=cap_rule)

    def obj_rule(md):
        return (
            sum(opening_cost[i] * md.open[i] for i in range(n_centers))
            + sum(transport_cost[i][j] * md.flow[i, j] for i in range(n_centers) for j in range(n_stores))
        )

    model.cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}