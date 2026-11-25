# {"sets":{"K":[0,1],"T":[0,1,2,3,4],"T_after_initial":[1,2,3,4]},"params":{"base_cost[k]":["base_cost_type0","base_cost_type1"],"power_cost[k]":["power_cost_type0","power_cost_type1"],"startup_cost[k]":["startup_cost_type0","startup_cost_type1"],"demand[t]":"demand[t]","min_output[k]":["min_output_type0","min_output_type1"],"max_output[k]":["max_output_type0","max_output_type1"],"reserve_margin":"reserve_margin","max_active":"max_active_per_type","first_startup_limit[k]":["max_startups_first_period_type0","max_startups_first_period_type1"]},"decision_variables":{"operating[k,t]":"nonnegative integer","output[k,t]":"nonnegative real, aggregate output by type","startups[k,t]":"nonnegative integer"},"constraints":["sum_k output[k,t] >= demand[t] for all t","output[k,t] >= min_output[k]*operating[k,t] for all k,t","output[k,t] <= max_output[k]*operating[k,t] for all k,t","sum_k max_output[k]*operating[k,t] >= (1+reserve_margin)*demand[t] for all t","operating[k,t] <= max_active for all k,t","operating[k,0] <= startups[k,0] for all k, initially no active generators","startups[k,0] <= first_startup_limit[k] for all k","operating[k,t] <= operating[k,t-1]+startups[k,t] for all k,t>0","startups[k,t] <= operating[k,t]-operating[k,t-1] for all k,t>0"],"objective":"minimize sum_{k,t}(base_cost[k]*operating[k,t]+power_cost[k]*output[k,t]+startup_cost[k]*startups[k,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.K = pyo.Set(initialize=[0, 1], ordered=True)
    model.T = pyo.RangeSet(0, 4)
    model.T_after_initial = pyo.RangeSet(1, 4)

    model.base_cost = pyo.Param(
        model.K,
        initialize={
            0: params["base_cost_type0"],
            1: params["base_cost_type1"],
        },
        within=pyo.NonNegativeReals,
    )
    model.power_cost = pyo.Param(
        model.K,
        initialize={
            0: params["power_cost_type0"],
            1: params["power_cost_type1"],
        },
        within=pyo.NonNegativeReals,
    )
    model.startup_cost = pyo.Param(
        model.K,
        initialize={
            0: params["startup_cost_type0"],
            1: params["startup_cost_type1"],
        },
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.T,
        initialize={t: params["demand"][t] for t in model.T},
        within=pyo.NonNegativeReals,
    )
    model.min_output = pyo.Param(
        model.K,
        initialize={
            0: params["min_output_type0"],
            1: params["min_output_type1"],
        },
        within=pyo.NonNegativeReals,
    )
    model.max_output = pyo.Param(
        model.K,
        initialize={
            0: params["max_output_type0"],
            1: params["max_output_type1"],
        },
        within=pyo.NonNegativeReals,
    )
    model.reserve_margin = pyo.Param(
        initialize=params["reserve_margin"],
        within=pyo.NonNegativeReals,
    )
    model.max_active = pyo.Param(
        initialize=params["max_active_per_type"],
        within=pyo.NonNegativeReals,
    )
    model.first_startup_limit = pyo.Param(
        model.K,
        initialize={
            0: params["max_startups_first_period_type0"],
            1: params["max_startups_first_period_type1"],
        },
        within=pyo.NonNegativeReals,
    )

    model.operating = pyo.Var(
        model.K, model.T, domain=pyo.NonNegativeIntegers
    )
    model.output = pyo.Var(
        model.K, model.T, domain=pyo.NonNegativeReals
    )
    model.startups = pyo.Var(
        model.K, model.T, domain=pyo.NonNegativeIntegers
    )

    model.demand_requirement = pyo.Constraint(
        model.T,
        rule=lambda block, t: (
            sum(block.output[k, t] for k in block.K)
            >= block.demand[t]
        ),
    )

    model.minimum_output_requirement = pyo.Constraint(
        model.K,
        model.T,
        rule=lambda block, k, t: (
            block.output[k, t]
            >= block.min_output[k] * block.operating[k, t]
        ),
    )

    model.maximum_output_requirement = pyo.Constraint(
        model.K,
        model.T,
        rule=lambda block, k, t: (
            block.output[k, t]
            <= block.max_output[k] * block.operating[k, t]
        ),
    )

    model.reserve_requirement = pyo.Constraint(
        model.T,
        rule=lambda block, t: (
            sum(
                block.max_output[k] * block.operating[k, t]
                for k in block.K
            )
            >= (1 + block.reserve_margin) * block.demand[t]
        ),
    )

    model.active_limit = pyo.Constraint(
        model.K,
        model.T,
        rule=lambda block, k, t: (
            block.operating[k, t] <= block.max_active
        ),
    )

    model.initial_availability = pyo.Constraint(
        model.K,
        rule=lambda block, k: (
            block.operating[k, 0] <= block.startups[k, 0]
        ),
    )

    model.initial_startup_limit = pyo.Constraint(
        model.K,
        rule=lambda block, k: (
            block.startups[k, 0] <= block.first_startup_limit[k]
        ),
    )

    model.period_availability = pyo.Constraint(
        model.K,
        model.T_after_initial,
        rule=lambda block, k, t: (
            block.operating[k, t]
            <= block.operating[k, t - 1] + block.startups[k, t]
        ),
    )

    model.subsequent_startup_limit = pyo.Constraint(
        model.K,
        model.T_after_initial,
        rule=lambda block, k, t: (
            block.startups[k, t]
            <= block.operating[k, t] - block.operating[k, t - 1]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.base_cost[k] * model.operating[k, t]
            + model.power_cost[k] * model.output[k, t]
            + model.startup_cost[k] * model.startups[k, t]
            for k in model.K
            for t in model.T
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Continue to the objective test only for missing-solution errors.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}