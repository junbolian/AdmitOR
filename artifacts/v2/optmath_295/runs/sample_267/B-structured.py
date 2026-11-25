# IR: {"sets":{"types":[0,1],"periods":[0,1,2,3,4]},"params":["fixed_cost_type0","fixed_cost_type1","variable_cost_type0","variable_cost_type1","start_cost_type0","start_cost_type1","demand","min_output_type0","max_output_type0","min_output_type1","max_output_type1","capacity_req","max_operational_type0","max_operational_type1","max_start_period0_type0","max_start_period0_type1"],"parameter_maps":{"fixed_cost[k]":"fixed_cost_type{k}","variable_cost[k]":"variable_cost_type{k}","start_cost[k]":"start_cost_type{k}","min_output[k]":"min_output_type{k}","max_output[k]":"max_output_type{k}","max_operational[k]":"max_operational_type{k}","initial_start_limit[k]":"max_start_period0_type{k}"},"variables":{"operational[k,t]":"nonnegative integer","power[k,t]":"nonnegative integer","started[k,t]":"nonnegative integer"},"constraints":["sum_k power[k,t] >= demand[t], all t","min_output[k]*operational[k,t] <= power[k,t], all k,t","power[k,t] <= max_output[k]*operational[k,t], all k,t","sum_k max_output[k]*operational[k,t] >= capacity_req[t], all t","operational[k,t] <= max_operational[k], all k,t","started[k,0] <= initial_start_limit[k], all k","operational[k,0] <= started[k,0], all k","started[k,t] <= operational[k,t-1], all k,t>0","operational[k,t] <= operational[k,t-1]+started[k,t], all k,t>0"],"objective":"minimize sum_{k,t}(fixed_cost[k]*operational[k,t]+variable_cost[k]*power[k,t]+start_cost[k]*started[k,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = {
        0: params["fixed_cost_type0"],
        1: params["fixed_cost_type1"],
    }
    variable_cost = {
        0: params["variable_cost_type0"],
        1: params["variable_cost_type1"],
    }
    start_cost = {
        0: params["start_cost_type0"],
        1: params["start_cost_type1"],
    }
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
    initial_start_limit = {
        0: params["max_start_period0_type0"],
        1: params["max_start_period0_type1"],
    }
    demand = params["demand"]
    capacity_req = params["capacity_req"]

    model = pyo.ConcreteModel()
    model.generator_types = pyo.Set(initialize=[0, 1], ordered=True)
    model.periods = pyo.RangeSet(0, 4)
    model.later_periods = pyo.RangeSet(1, 4)

    model.operational = pyo.Var(
        model.generator_types, model.periods, domain=pyo.NonNegativeIntegers
    )
    model.power = pyo.Var(
        model.generator_types, model.periods, domain=pyo.NonNegativeIntegers
    )
    model.started = pyo.Var(
        model.generator_types, model.periods, domain=pyo.NonNegativeIntegers
    )

    def demand_rule(block, period):
        return sum(
            block.power[kind, period] for kind in block.generator_types
        ) >= demand[period]

    model.demand_constraint = pyo.Constraint(model.periods, rule=demand_rule)

    def minimum_output_rule(block, kind, period):
        return (
            block.power[kind, period]
            >= min_output[kind] * block.operational[kind, period]
        )

    model.minimum_output_constraint = pyo.Constraint(
        model.generator_types, model.periods, rule=minimum_output_rule
    )

    def maximum_output_rule(block, kind, period):
        return (
            block.power[kind, period]
            <= max_output[kind] * block.operational[kind, period]
        )

    model.maximum_output_constraint = pyo.Constraint(
        model.generator_types, model.periods, rule=maximum_output_rule
    )

    def capacity_rule(block, period):
        return sum(
            max_output[kind] * block.operational[kind, period]
            for kind in block.generator_types
        ) >= capacity_req[period]

    model.capacity_constraint = pyo.Constraint(model.periods, rule=capacity_rule)

    def operational_limit_rule(block, kind, period):
        return block.operational[kind, period] <= max_operational[kind]

    model.operational_limit_constraint = pyo.Constraint(
        model.generator_types, model.periods, rule=operational_limit_rule
    )

    def initial_start_limit_rule(block, kind):
        return block.started[kind, 0] <= initial_start_limit[kind]

    model.initial_start_limit_constraint = pyo.Constraint(
        model.generator_types, rule=initial_start_limit_rule
    )

    def initial_operational_rule(block, kind):
        return block.operational[kind, 0] <= block.started[kind, 0]

    model.initial_operational_constraint = pyo.Constraint(
        model.generator_types, rule=initial_operational_rule
    )

    def subsequent_start_limit_rule(block, kind, period):
        return block.started[kind, period] <= block.operational[kind, period - 1]

    model.subsequent_start_limit_constraint = pyo.Constraint(
        model.generator_types,
        model.later_periods,
        rule=subsequent_start_limit_rule,
    )

    def operational_transition_rule(block, kind, period):
        return (
            block.operational[kind, period]
            <= block.operational[kind, period - 1] + block.started[kind, period]
        )

    model.operational_transition_constraint = pyo.Constraint(
        model.generator_types,
        model.later_periods,
        rule=operational_transition_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            fixed_cost[kind] * model.operational[kind, period]
            + variable_cost[kind] * model.power[kind, period]
            + start_cost[kind] * model.started[kind, period]
            for kind in model.generator_types
            for period in model.periods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}