import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    T = 5
    types = [0, 1]

    base_cost = {
        0: params["base_cost_type0"],
        1: params["base_cost_type1"],
    }
    power_cost = {
        0: params["power_cost_type0"],
        1: params["power_cost_type1"],
    }
    startup_cost = {
        0: params["startup_cost_type0"],
        1: params["startup_cost_type1"],
    }
    demand = params["demand"]
    min_out = {
        0: params["min_output_type0"],
        1: params["min_output_type1"],
    }
    max_out = {
        0: params["max_output_type0"],
        1: params["max_output_type1"],
    }
    reserve_margin = params["reserve_margin"]
    max_active = params["max_active_per_type"]
    max_startup_first = {
        0: params["max_startups_first_period_type0"],
        1: params["max_startups_first_period_type1"],
    }

    model = pyo.ConcreteModel()

    model.T = pyo.RangeSet(0, T - 1)
    model.K = pyo.Set(initialize=types)

    # Decision variables
    model.n = pyo.Var(model.K, model.T, domain=pyo.NonNegativeIntegers)   # active count
    model.u = pyo.Var(model.K, model.T, domain=pyo.NonNegativeIntegers)   # startups
    model.p = pyo.Var(model.K, model.T, domain=pyo.NonNegativeReals)      # power output

    # Demand satisfaction
    def demand_rule(mdl, t):
        return sum(mdl.p[k, t] for k in mdl.K) >= demand[t]
    model.demand_con = pyo.Constraint(model.T, rule=demand_rule)

    # Reserve margin: total max capacity >= (1 + reserve_margin) * demand
    def reserve_rule(mdl, t):
        return sum(max_out[k] * mdl.n[k, t] for k in mdl.K) >= (1.0 + reserve_margin) * demand[t]
    model.reserve_con = pyo.Constraint(model.T, rule=reserve_rule)

    # Power output bounds given active status
    def pmin_rule(mdl, k, t):
        return mdl.p[k, t] >= min_out[k] * mdl.n[k, t]
    model.pmin_con = pyo.Constraint(model.K, model.T, rule=pmin_rule)

    def pmax_rule(mdl, k, t):
        return mdl.p[k, t] <= max_out[k] * mdl.n[k, t]
    model.pmax_con = pyo.Constraint(model.K, model.T, rule=pmax_rule)

    # Max active per type per period
    def max_active_rule(mdl, k, t):
        return mdl.n[k, t] <= max_active
    model.max_active_con = pyo.Constraint(model.K, model.T, rule=max_active_rule)

    # Startup balance: n[k,t] <= n[k,t-1] + u[k,t]
    def startup_balance_rule(mdl, k, t):
        if t == 0:
            return pyo.Constraint.Skip
        return mdl.n[k, t] <= mdl.n[k, t - 1] + mdl.u[k, t]
    model.startup_balance_con = pyo.Constraint(model.K, model.T, rule=startup_balance_rule)

    # Startup non-negativity relative to increase: u[k,t] >= n[k,t] - n[k,t-1] is implied by balance; enforce lower implied
    def startup_increase_rule(mdl, k, t):
        if t == 0:
            return pyo.Constraint.Skip
        return mdl.u[k, t] >= mdl.n[k, t] - mdl.n[k, t - 1]
    model.startup_increase_con = pyo.Constraint(model.K, model.T, rule=startup_increase_rule)

    # First period startup limits
    def first_startup_rule(mdl, k):
        return mdl.u[k, 0] <= max_startup_first[k]
    model.first_startup_con = pyo.Constraint(model.K, rule=first_startup_rule)

    # First period active must be at most startups in first period (n[k,0] <= u[k,0])
    def first_active_rule(mdl, k):
        return mdl.n[k, 0] <= mdl.u[k, 0]
    model.first_active_con = pyo.Constraint(model.K, rule=first_active_rule)

    # Objective
    def obj_rule(mdl):
        return sum(
            base_cost[k] * mdl.n[k, t]
            + power_cost[k] * mdl.p[k, t]
            + startup_cost[k] * mdl.u[k, t]
            for k in mdl.K for t in mdl.T
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}