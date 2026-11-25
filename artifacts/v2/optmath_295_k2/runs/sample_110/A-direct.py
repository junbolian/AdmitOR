import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    base_cost = {0: params["base_cost_type0"], 1: params["base_cost_type1"]}
    power_cost = {0: params["power_cost_type0"], 1: params["power_cost_type1"]}
    startup_cost = {0: params["startup_cost_type0"], 1: params["startup_cost_type1"]}
    demand = params["demand"]
    min_out = {0: params["min_output_type0"], 1: params["min_output_type1"]}
    max_out = {0: params["max_output_type0"], 1: params["max_output_type1"]}
    reserve_margin = params["reserve_margin"]
    max_active = params["max_active_per_type"]
    max_start_first = {
        0: params["max_startups_first_type0"],
        1: params["max_startups_first_type1"],
    }

    periods = list(range(5))
    types = [0, 1]

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=periods)
    model.T = pyo.Set(initialize=types)

    model.n_active = pyo.Var(model.P, model.T, domain=pyo.NonNegativeIntegers)
    model.n_start = pyo.Var(model.P, model.T, domain=pyo.NonNegativeIntegers)
    model.gen_output = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    def base_obj(m):
        return sum(
            base_cost[t] * m.n_active[p, t]
            + power_cost[t] * m.gen_output[p, t]
            + startup_cost[t] * m.n_start[p, t]
            for p in m.P
            for t in m.T
        )

    model.total_cost = pyo.Objective(rule=base_obj, sense=pyo.minimize)

    def demand_rule(m, p):
        return sum(m.gen_output[p, t] for t in m.T) >= demand[p]

    model.demand_con = pyo.Constraint(model.P, rule=demand_rule)

    def reserve_rule(m, p):
        return (
            sum(max_out[t] * m.n_active[p, t] for t in m.T)
            >= (1 + reserve_margin) * demand[p]
        )

    model.reserve_con = pyo.Constraint(model.P, rule=reserve_rule)

    def output_upper_rule(m, p, t):
        return m.gen_output[p, t] <= max_out[t] * m.n_active[p, t]

    model.output_upper_con = pyo.Constraint(model.P, model.T, rule=output_upper_rule)

    def output_lower_rule(m, p, t):
        return m.gen_output[p, t] >= min_out[t] * m.n_active[p, t]

    model.output_lower_con = pyo.Constraint(model.P, model.T, rule=output_lower_rule)

    def max_active_rule(m, p, t):
        return m.n_active[p, t] <= max_active

    model.max_active_con = pyo.Constraint(model.P, model.T, rule=max_active_rule)

    def transition_rule(m, p, t):
        if p == 0:
            return pyo.Constraint.Skip
        return m.n_active[p, t] <= m.n_active[p - 1, t] + m.n_start[p, t]

    model.transition_con = pyo.Constraint(model.P, model.T, rule=transition_rule)

    def start_first_rule(m, t):
        return m.n_start[0, t] <= max_start_first[t]

    model.start_first_con = pyo.Constraint(model.T, rule=start_first_rule)

    def start_subseq_rule(m, p, t):
        if p == 0:
            return pyo.Constraint.Skip
        return m.n_start[p, t] >= m.n_active[p, t] - m.n_active[p - 1, t]

    model.start_subseq_con = pyo.Constraint(model.P, model.T, rule=start_subseq_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}