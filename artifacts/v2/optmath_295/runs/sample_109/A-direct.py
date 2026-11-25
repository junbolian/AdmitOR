import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    base_cost = params["base_cost"]
    per_mw_cost = params["per_mw_cost"]
    startup_cost = params["startup_cost"]
    demand = params["demand"]
    reserve_demand = params["reserve_demand"]
    min_output = params["min_output"]
    max_output = params["max_output"]
    max_generators = params["max_generators"]
    initial_startup_allowance = params["initial_startup_allowance"]

    T = range(5)
    G = range(3)

    model = pyo.ConcreteModel()

    model.T = pyo.Set(initialize=list(T))
    model.G = pyo.Set(initialize=list(G))

    model.n = pyo.Var(model.G, model.T, domain=pyo.NonNegativeIntegers)
    model.s = pyo.Var(model.G, model.T, domain=pyo.NonNegativeIntegers)
    model.p = pyo.Var(model.G, model.T, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(
            base_cost[g] * mdl.n[g, t]
            + per_mw_cost[g] * mdl.p[g, t]
            + startup_cost[g] * mdl.s[g, t]
            for g in mdl.G
            for t in mdl.T
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(mdl, t):
        return sum(mdl.p[g, t] for g in mdl.G) >= demand[t]

    model.demand_con = pyo.Constraint(model.T, rule=demand_rule)

    def reserve_rule(mdl, t):
        return sum(max_output[g] * mdl.n[g, t] for g in mdl.G) >= reserve_demand[t]

    model.reserve_con = pyo.Constraint(model.T, rule=reserve_rule)

    def max_gen_rule(mdl, g, t):
        return mdl.n[g, t] <= max_generators[g]

    model.max_gen_con = pyo.Constraint(model.G, model.T, rule=max_gen_rule)

    def p_min_rule(mdl, g, t):
        return mdl.p[g, t] >= min_output[g] * mdl.n[g, t]

    model.p_min_con = pyo.Constraint(model.G, model.T, rule=p_min_rule)

    def p_max_rule(mdl, g, t):
        return mdl.p[g, t] <= max_output[g] * mdl.n[g, t]

    model.p_max_con = pyo.Constraint(model.G, model.T, rule=p_max_rule)

    def startup_rule(mdl, g, t):
        if t == 0:
            return mdl.n[g, t] <= mdl.s[g, t] + initial_startup_allowance[g]
        return mdl.n[g, t] <= mdl.n[g, t - 1] + mdl.s[g, t]

    model.startup_con = pyo.Constraint(model.G, model.T, rule=startup_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}