import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n = len(supply)
    m = len(demand)

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, n - 1)
    model.J = pyo.RangeSet(0, m - 1)

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def obj_rule(model):
        return sum(cost[i][j] * model.x[i, j] for i in model.I for j in model.J)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(model, i):
        return sum(model.x[i, j] for j in model.J) == supply[i]

    model.supply_con = pyo.Constraint(model.I, rule=supply_rule)

    def demand_rule(model, j):
        return sum(model.x[i, j] for i in model.I) == demand[j]

    model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}