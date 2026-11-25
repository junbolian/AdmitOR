import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    periods = list(range(5))
    types = [0, 1]

    fixed_cost = {
        0: params["fixed_cost_type0"],
        1: params["fixed_cost_type1"],
    }
    var_cost = {
        0: params["var_cost_type0"],
        1: params["var_cost_type1"],
    }
    start_cost = {
        0: params["start_cost_type0"],
        1: params["start_cost_type1"],
    }
    demand = {
        0: params["demand"],
        # demand is a per-period quantity; if scalar use it, else map.
    }
    # Handle demand possibly given as scalar or per-period
    demand_param = params["demand"]
    if isinstance(demand_param, (list, tuple)):
        demand = {t: demand_param[t] for t in periods}
    else:
        demand = {t: demand_param for t in periods}

    capac_req_param = params["capac_req"]
    if isinstance(capac_req_param, (list, tuple)):
        capac_req = {t: capac_req_param[t] for t in periods}
    else:
        capac_req = {t: capac_req_param for t in periods}

    min_output = {
        0: params["min_output_type0"],
        1: params["min_output_type1"],
    }
    max_output = {
        0: params["max_output_type0"],
        1: params["max_output_type1"],
    }
    max_operational = {
        0: params["max_operational_type0"],
        1: params["max_operational_type1"],
    }
    max_start_period0 = {
        0: params["max_start_period0_type0"],
        1: params["max_start_period0_type1"],
    }

    model = pyo.ConcreteModel()

    model.T = pyo.Set(initialize=periods)
    model.K = pyo.Set(initialize=types)

    model.n = pyo.Var(model.T, model.K, domain=pyo.NonNegativeIntegers)
    model.s = pyo.Var(model.T, model.K, domain=pyo.NonNegativeIntegers)
    model.p = pyo.Var(model.T, model.K, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(
            fixed_cost[k] * mdl.n[t, k]
            + var_cost[k] * mdl.p[t, k]
            + start_cost[k] * mdl.s[t, k]
            for t in mdl.T
            for k in mdl.K
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Demand satisfaction
    def demand_rule(mdl, t):
        return sum(mdl.p[t, k] for k in mdl.K) >= demand[t]

    model.c_demand = pyo.Constraint(model.T, rule=demand_rule)

    # Capacity requirement
    def capacity_rule(mdl, t):
        return sum(max_output[k] * mdl.n[t, k] for k in mdl.K) >= capac_req[t]

    model.c_capacity = pyo.Constraint(model.T, rule=capacity_rule)

    # Output bounds when operational
    def out_lb_rule(mdl, t, k):
        return mdl.p[t, k] >= min_output[k] * mdl.n[t, k]

    def out_ub_rule(mdl, t, k):
        return mdl.p[t, k] <= max_output[k] * mdl.n[t, k]

    model.c_out_lb = pyo.Constraint(model.T, model.K, rule=out_lb_rule)
    model.c_out_ub = pyo.Constraint(model.T, model.K, rule=out_ub_rule)

    # Max operational
    def max_op_rule(mdl, t, k):
        return mdl.n[t, k] <= max_operational[k]

    model.c_max_op = pyo.Constraint(model.T, model.K, rule=max_op_rule)

    # Period 0 start limits
    def start_p0_rule(mdl, k):
        return mdl.s[0, k] <= max_start_period0[k]

    model.c_start_p0 = pyo.Constraint(model.K, rule=start_p0_rule)

    # Subsequent period start limits
    def start_later_rule(mdl, t, k):
        if t == 0:
            return pyo.Constraint.Skip
        return mdl.s[t, k] <= mdl.n[t - 1, k]

    model.c_start_later = pyo.Constraint(model.T, model.K, rule=start_later_rule)

    # Operational balance: n_t <= n_{t-1} + s_t
    def balance_rule(mdl, t, k):
        if t == 0:
            return mdl.n[t, k] <= mdl.s[t, k]
        return mdl.n[t, k] <= mdl.n[t - 1, k] + mdl.s[t, k]

    model.c_balance = pyo.Constraint(model.T, model.K, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}