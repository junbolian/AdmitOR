import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    num_facilities = len(supply)
    num_centers = len(demand)

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, num_facilities - 1)
    model.J = pyo.RangeSet(0, num_centers - 1)

    def flow_bounds(m, i, j):
        return (0, capacity[i][j])

    model.x = pyo.Var(model.I, model.J, bounds=flow_bounds)

    def transport_cost_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.I for j in m.J)

    model.transport_cost = pyo.Objective(rule=transport_cost_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.J) == supply[i]

    model.supply_con = pyo.Constraint(model.I, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.I) == demand[j]

    model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.transport_cost))
    return {"objective": obj_val, "status": "optimal"}