# IR: {"sets":{"K":[0,1],"T":"range(params['num_periods'])"},"params":{"base_cost":["base_cost_type0","base_cost_type1"],"var_cost":["var_cost_type0","var_cost_type1"],"startup_cost":["startup_cost_type0","startup_cost_type1"],"max_units":["max_units_type0","max_units_type1"],"min_output":["min_output_type0","min_output_type1"],"max_output":["max_output_type0","max_output_type1"],"initial_startup_cap":["max_startup_type0_period0","max_startup_type1_period0"],"demand":"demand[t]","reserve_margin":"reserve_margin","num_periods":"num_periods"},"variables":{"operating[k,t]":"nonnegative integer, <= max_units[k]","generation[k,t]":"nonnegative real","startups[k,t]":"nonnegative integer"},"constraints":["sum_k generation[k,t] >= demand[t]","generation[k,t] >= min_output[k]*operating[k,t]","generation[k,t] <= max_output[k]*operating[k,t]","sum_k max_output[k]*operating[k,t] >= (1+reserve_margin)*demand[t]","startups[k,0] = operating[k,0] (initially all units off)","startups[k,0] <= initial_startup_cap[k]","startups[k,t] >= operating[k,t]-operating[k,t-1], t>0","startups[k,t] <= operating[k,t-1], t>0"],"objective":"min sum_{k,t}(base_cost[k]*operating[k,t]+var_cost[k]*generation[k,t]+startup_cost[k]*startups[k,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_periods = int(params["num_periods"])
    if num_periods != params["num_periods"] or num_periods < 1:
        raise ValueError("num_periods must be a positive integer.")

    base_cost = {
        0: params["base_cost_type0"],
        1: params["base_cost_type1"],
    }
    var_cost = {
        0: params["var_cost_type0"],
        1: params["var_cost_type1"],
    }
    startup_cost = {
        0: params["startup_cost_type0"],
        1: params["startup_cost_type1"],
    }
    max_units = {
        0: params["max_units_type0"],
        1: params["max_units_type1"],
    }
    min_output = {
        0: params["min_output_type0"],
        1: params["min_output_type1"],
    }
    max_output = {
        0: params["max_output_type0"],
        1: params["max_output_type1"],
    }
    initial_startup_cap = {
        0: params["max_startup_type0_period0"],
        1: params["max_startup_type1_period0"],
    }
    demand = params["demand"]
    reserve_margin = params["reserve_margin"]

    model = pyo.ConcreteModel()
    model.K = pyo.Set(initialize=(0, 1), ordered=True)
    model.T = pyo.Set(initialize=range(num_periods), ordered=True)

    model.base_cost = pyo.Param(model.K, initialize=base_cost)
    model.var_cost = pyo.Param(model.K, initialize=var_cost)
    model.startup_cost = pyo.Param(model.K, initialize=startup_cost)
    model.max_units = pyo.Param(
        model.K, initialize=max_units, within=pyo.NonNegativeIntegers
    )
    model.min_output = pyo.Param(model.K, initialize=min_output)
    model.max_output = pyo.Param(model.K, initialize=max_output)
    model.initial_startup_cap = pyo.Param(
        model.K, initialize=initial_startup_cap, within=pyo.NonNegativeIntegers
    )
    model.demand = pyo.Param(
        model.T, initialize={period: demand[period] for period in range(num_periods)}
    )
    model.reserve_margin = pyo.Param(initialize=reserve_margin)

    model.operating = pyo.Var(
        model.K,
        model.T,
        domain=pyo.NonNegativeIntegers,
        bounds=lambda mdl, kind, period: (0, mdl.max_units[kind]),
    )
    model.generation = pyo.Var(
        model.K, model.T, domain=pyo.NonNegativeReals
    )
    model.startups = pyo.Var(
        model.K, model.T, domain=pyo.NonNegativeIntegers
    )

    model.demand_requirement = pyo.Constraint(
        model.T,
        rule=lambda mdl, period: (
            sum(mdl.generation[kind, period] for kind in mdl.K)
            >= mdl.demand[period]
        ),
    )
    model.minimum_generation = pyo.Constraint(
        model.K,
        model.T,
        rule=lambda mdl, kind, period: (
            mdl.generation[kind, period]
            >= mdl.min_output[kind] * mdl.operating[kind, period]
        ),
    )
    model.maximum_generation = pyo.Constraint(
        model.K,
        model.T,
        rule=lambda mdl, kind, period: (
            mdl.generation[kind, period]
            <= mdl.max_output[kind] * mdl.operating[kind, period]
        ),
    )
    model.reserve_requirement = pyo.Constraint(
        model.T,
        rule=lambda mdl, period: (
            sum(
                mdl.max_output[kind] * mdl.operating[kind, period]
                for kind in mdl.K
            )
            >= (1 + mdl.reserve_margin) * mdl.demand[period]
        ),
    )

    model.initial_startup_balance = pyo.Constraint(
        model.K,
        rule=lambda mdl, kind: mdl.startups[kind, 0] == mdl.operating[kind, 0],
    )
    model.initial_startup_limit = pyo.Constraint(
        model.K,
        rule=lambda mdl, kind: (
            mdl.startups[kind, 0] <= mdl.initial_startup_cap[kind]
        ),
    )

    def startup_requirement_rule(mdl, kind, period):
        if period == 0:
            return pyo.Constraint.Skip
        return (
            mdl.startups[kind, period]
            >= mdl.operating[kind, period] - mdl.operating[kind, period - 1]
        )

    model.startup_requirement = pyo.Constraint(
        model.K, model.T, rule=startup_requirement_rule
    )

    def subsequent_startup_limit_rule(mdl, kind, period):
        if period == 0:
            return pyo.Constraint.Skip
        return mdl.startups[kind, period] <= mdl.operating[kind, period - 1]

    model.subsequent_startup_limit = pyo.Constraint(
        model.K, model.T, rule=subsequent_startup_limit_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.base_cost[kind] * model.operating[kind, period]
            + model.var_cost[kind] * model.generation[kind, period]
            + model.startup_cost[kind] * model.startups[kind, period]
            for kind in model.K
            for period in model.T
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when it cannot load a feasible solution.
        # Preserve unexpected RuntimeErrors for the calling harness.
        if "a feasible solution was not found" not in str(exc).lower():
            raise
        return {"objective": None, "status": "no_feasible_solution"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}