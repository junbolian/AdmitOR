import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    T = 5
    types = [0, 1, 2]

    base_cost = params["base_cost"]
    marginal_cost = params["marginal_cost"]
    startup_cost = params["startup_cost"]
    demand = params["demand"]
    min_output = params["min_output"]
    max_output = params["max_output"]
    max_generators = params["max_generators"]
    reserve_requirement = params["reserve_requirement"]
    initial_startup_bound = params["initial_startup_bound"]

    model = pyo.ConcreteModel()
    model.T = pyo.RangeSet(0, T - 1)
    model.K = pyo.Set(initialize=types)

    model.n = pyo.Var(model.K, model.T, domain=pyo.NonNegativeIntegers)
    model.s = pyo.Var(model.K, model.T, domain=pyo.NonNegativeIntegers)
    model.p = pyo.Var(model.K, model.T, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        total = 0
        for k in m.K:
            for t in m.T:
                total += base_cost[k] * m.n[k, t]
                total += marginal_cost[k] * m.p[k, t]
                total += startup_cost[k] * m.s[k, t]
        return total
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, t):
        return sum(m.p[k, t] for k in m.K) >= demand[t]
    model.demand_con = pyo.Constraint(model.T, rule=demand_rule)

    def reserve_rule(m, t):
        return sum(max_output[k] * m.n[k, t] for k in m.K) >= reserve_requirement[t]
    model.reserve_con = pyo.Constraint(model.T, rule=reserve_rule)

    def cap_lower_rule(m, k, t):
        return m.p[k, t] >= min_output[k] * m.n[k, t]
    model.cap_lower_con = pyo.Constraint(model.K, model.T, rule=cap_lower_rule)

    def cap_upper_rule(m, k, t):
        return m.p[k, t] <= max_output[k] * m.n[k, t]
    model.cap_upper_con = pyo.Constraint(model.K, model.T, rule=cap_upper_rule)

    def maxgen_rule(m, k, t):
        return m.n[k, t] <= max_generators[k]
    model.maxgen_con = pyo.Constraint(model.K, model.T, rule=maxgen_rule)

    def startup_init_rule(m, k):
        return m.n[k, 0] <= m.s[k, 0] + initial_startup_bound[k]
    model.startup_init_con = pyo.Constraint(model.K, rule=startup_init_rule)

    def startup_sub_rule(m, k, t):
        return m.n[k, t] <= m.n[k, t - 1] + m.s[k, t]
    model.startup_sub_con = pyo.Constraint(model.K, model.T, rule=lambda m, k, t: pyo.Constraint.Skip if t == 0 else startup_sub_rule(m, k, t))

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}