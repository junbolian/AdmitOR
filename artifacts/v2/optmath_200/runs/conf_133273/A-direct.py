import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    nO = len(supply)
    nD = len(demand)

    model = pyo.ConcreteModel()
    model.O = pyo.RangeSet(0, nO - 1)
    model.D = pyo.RangeSet(0, nD - 1)

    def x_bounds(m, i, j):
        return (0, capacity[i][j])

    model.x = pyo.Var(model.O, model.D, domain=pyo.NonNegativeReals, bounds=x_bounds)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.O for j in m.D)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.D) == supply[i]

    model.supply_con = pyo.Constraint(model.O, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.O) == demand[j]

    model.demand_con = pyo.Constraint(model.D, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}