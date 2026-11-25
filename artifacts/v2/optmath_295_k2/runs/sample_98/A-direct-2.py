import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    production_cost = params["production_cost"]
    setup_cost = params["setup_cost"]
    holding_cost = params["holding_cost"]
    capacity = params["capacity"]
    capacity_consumption = params["capacity_consumption"]

    products = list(range(len(demand)))
    months = list(range(len(demand[0])))

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=products)
    model.M = pyo.Set(initialize=months)

    model.x = pyo.Var(model.P, model.M, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.M, domain=pyo.Binary)
    model.inv = pyo.Var(model.P, model.M, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return (
            sum(production_cost[p][t] * mdl.x[p, t]
                for p in mdl.P for t in mdl.M)
            + sum(setup_cost[p][t] * mdl.y[p, t]
                  for p in mdl.P for t in mdl.M)
            + sum(holding_cost[p] * mdl.inv[p, t]
                  for p in mdl.P for t in mdl.M)
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cap_rule(mdl, t):
        return sum(capacity_consumption[p] * mdl.x[p, t] for p in mdl.P) <= capacity[t]

    model.cap_con = pyo.Constraint(model.M, rule=cap_rule)

    def balance_rule(mdl, p, t):
        return sum(mdl.x[p, k] for k in mdl.M if k <= t) - mdl.inv[p, t] == \
            sum(demand[p][k] for k in mdl.M if k <= t)

    model.balance_con = pyo.Constraint(model.P, model.M, rule=balance_rule)

    def link_rule(mdl, p, t):
        max_qty = sum(demand[p][k] for k in mdl.M if k >= t)
        return mdl.x[p, t] <= max_qty * mdl.y[p, t]

    model.link_con = pyo.Constraint(model.P, model.M, rule=link_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}