import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    shipping_cost = params["shipping_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_fac = len(fixed_cost)
    n_cust = len(demand)

    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, n_fac - 1)
    model.C = pyo.RangeSet(0, n_cust - 1)

    model.y = pyo.Var(model.F, domain=pyo.Binary)
    model.x = pyo.Var(model.F, model.C, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(fixed_cost[i] * mdl.y[i] for i in mdl.F) + sum(
            shipping_cost[i][j] * mdl.x[i, j] for i in mdl.F for j in mdl.C
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.F) == demand[j]

    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def capacity_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.C) <= capacity[i] * mdl.y[i]

    model.capacity_con = pyo.Constraint(model.F, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}