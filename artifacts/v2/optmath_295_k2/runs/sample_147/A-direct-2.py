import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    periods = range(4)
    gen_types = [0, 1]

    base_cost = {0: params["base_cost_type0"], 1: params["base_cost_type1"]}
    var_cost = {0: params["var_cost_type0"], 1: params["var_cost_type1"]}
    startup_cost = {0: params["startup_cost_type0"], 1: params["startup_cost_type1"]}
    max_units = {0: params["max_units_type0"], 1: params["max_units_type1"]}
    min_output = {0: params["min_output_type0"], 1: params["min_output_type1"]}
    max_output = {0: params["max_output_type0"], 1: params["max_output_type1"]}
    demand = params["demand"]
    reserve_margin = params["reserve_margin"]
    max_startup_p0 = {0: params["max_startup_type0_period0"], 1: params["max_startup_type1_period0"]}

    model = pyo.ConcreteModel()

    model.T = pyo.Set(initialize=list(periods))
    model.G = pyo.Set(initialize=gen_types)

    model.n = pyo.Var(model.T, model.G, domain=pyo.NonNegativeIntegers)
    model.u = pyo.Var(model.T, model.G, domain=pyo.NonNegativeIntegers)
    model.p = pyo.Var(model.T, model.G, domain=pyo.NonNegativeReals)

    # Startup definition for period 0: u[0] <= n[0], and capped.
    def startup_p0_rule(m, g):
        return m.u[0, g] <= max_startup_p0[g]
    model.startup_p0 = pyo.Constraint(model.G, rule=startup_p0_rule)

    # For period 0, startups equals initial activation count: u[0] <= n[0]
    def u_le_n_p0_rule(m, g):
        return m.u[0, g] <= m.n[0, g]
    model.u_ln_p0 = pyo.Constraint(model.G, rule=u_le_n_p0_rule)

    # Startup flow constraints for subsequent periods
    def startup_flow_rule(m, t, g):
        if t == 0:
            return pyo.Constraint.Skip
        return m.u[t, g] >= m.n[t, g] - m.n[t - 1, g]
    model.startup_flow = pyo.Constraint(model.T, model.G, rule=startup_flow_rule)

    def startup_bound_rule(m, t, g):
        if t == 0:
            return pyo.Constraint.Skip
        return m.u[t, g] <= m.n[t - 1, g]
    model.startup_bound = pyo.Constraint(model.T, model.G, rule=startup_bound_rule)

    def max_units_rule(m, t, g):
        return m.n[t, g] <= max_units[g]
    model.max_units_c = pyo.Constraint(model.T, model.G, rule=max_units_rule)

    # Demand satisfaction
    def demand_rule(m, t):
        return sum(m.p[t, g] for g in m.G) >= demand[t]
    model.demand_c = pyo.Constraint(model.T, rule=demand_rule)

    # Minimum output when operating
    def min_output_rule(m, t, g):
        return m.p[t, g] >= min_output[g] * m.n[t, g]
    model.min_out_c = pyo.Constraint(model.T, model.G, rule=min_output_rule)

    # Maximum output when operating
    def max_output_rule(m, t, g):
        return m.p[t, g] <= max_output[g] * m.n[t, g]
    model.max_out_c = pyo.Constraint(model.T, model.G, rule=max_output_rule)

    # Reserve margin: total max possible output capacity >= demand * (1 + margin)
    def reserve_rule(m, t):
        return sum(max_output[g] * m.n[t, g] for g in m.G) >= demand[t] * (1 + reserve_margin)
    model.reserve_c = pyo.Constraint(model.T, rule=reserve_rule)

    def obj_rule(m):
        return sum(
            base_cost[g] * m.n[t, g]
            + var_cost[g] * m.p[t, g]
            + startup_cost[g] * m.u[t, g]
            for t in m.T for g in m.G
        )
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}