import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    production_cost = params["production_cost"]
    setup_cost = params["setup_cost"]
    holding_cost = params["holding_cost"]
    cumulative_demand = params["cumulative_demand"]
    resource_capacity = params["resource_capacity"]
    resource_consumption = params["resource_consumption"]
    max_production_if_setup = params["max_production_if_setup"]

    num_products = 3
    num_periods = 5
    products = range(num_products)
    periods = range(num_periods)

    def pc(p, t):
        v = production_cost[p]
        if isinstance(v, (list, tuple)):
            return v[t]
        return v[t] if not isinstance(v, dict) else v[t]

    def sc(p, t):
        v = setup_cost[p]
        if isinstance(v, (list, tuple)):
            return v[t]
        return v[t]

    def hc(p, t):
        v = holding_cost[p]
        if isinstance(v, (list, tuple)):
            return v[t]
        return v[t]

    def cd(p, t):
        v = cumulative_demand[p]
        if isinstance(v, (list, tuple)):
            return v[t]
        return v[t]

    def rc(t):
        return resource_capacity[t]

    def ru(p):
        return resource_consumption[p]

    def mx(p, t):
        v = max_production_if_setup[p]
        if isinstance(v, (list, tuple)):
            return v[t]
        return v[t]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=list(products))
    model.T = pyo.Set(initialize=list(periods))

    model.produce = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.setup = pyo.Var(model.P, model.T, domain=pyo.Binary)
    model.inventory = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    def prod_cost_rule(mdl):
        return sum(pc(p, t) * mdl.produce[p, t] for p in mdl.P for t in mdl.T)

    def setup_cost_rule(mdl):
        return sum(sc(p, t) * mdl.setup[p, t] for p in mdl.P for t in mdl.T)

    def holding_cost_rule(mdl):
        return sum(hc(p, t) * mdl.inventory[p, t] for p in mdl.P for t in mdl.T)

    model.obj = pyo.Objective(
        expr=prod_cost_rule(model) + setup_cost_rule(model) + holding_cost_rule(model),
        sense=pyo.minimize,
    )

    def linking_rule(mdl, p, t):
        return mdl.produce[p, t] <= mx(p, t) * mdl.setup[p, t]

    model.linking = pyo.Constraint(model.P, model.T, rule=linking_rule)

    def resource_rule(mdl, t):
        return sum(ru(p) * mdl.produce[p, t] for p in mdl.P) <= rc(t)

    model.resource = pyo.Constraint(model.T, rule=resource_rule)

    def balance_rule(mdl, p, t):
        if t == 0:
            return mdl.inventory[p, t] == mdl.produce[p, t] - cd(p, t)
        return mdl.inventory[p, t] == mdl.inventory[p, t - 1] + mdl.produce[p, t] - (
            cd(p, t) - cd(p, t - 1)
        )

    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    def final_inv_rule(mdl, p):
        return mdl.inventory[p, num_periods - 1] == 0

    model.final_inv = pyo.Constraint(model.P, rule=final_inv_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}