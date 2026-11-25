import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    capacity = params["capacity"]
    variable_cost = params["variable_cost"]

    n_fac = len(fixed_cost)
    n_cus = len(demand)
    facilities = range(n_fac)
    customers = range(n_cus)

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=list(facilities))
    model.C = pyo.Set(initialize=list(customers))

    model.y = pyo.Var(model.F, domain=pyo.Binary)
    model.x = pyo.Var(model.F, model.C, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(fixed_cost[f] * m.y[f] for f in m.F) + sum(
            variable_cost[f][c] * m.x[f, c] for f in m.F for c in m.C
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, c):
        return sum(m.x[f, c] for f in m.F) == demand[c]

    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def cap_rule(m, f):
        return sum(m.x[f, c] for c in m.C) <= capacity[f] * m.y[f]

    model.cap_con = pyo.Constraint(model.F, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}