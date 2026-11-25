# IR: {"sets":{"types":[0,1],"periods":[0,1,2,3]},"params":["base_cost_type0","base_cost_type1","var_cost","startup_cost_type0","startup_cost_type1","demand","min_output_type0","max_output_type0","min_output_type1","max_output_type1","reserve_margin","max_operating_type0","max_operating_type1","type1_initial_slack"],"assumptions":["Type 0 generators are initially off because no initial availability parameter is provided."],"variables":{"operating[type,period]":"NonNegativeIntegers","power[type,period]":"NonNegativeReals","started[type,period]":"NonNegativeIntegers"},"constraints":["sum_type power[type,period] >= demand[period]","power[type,period] >= min_output[type]*operating[type,period]","power[type,period] <= max_output[type]*operating[type,period]","sum_type max_output[type]*operating[type,period] >= (1+reserve_margin)*demand[period]","operating[type,period] <= max_operating[type]","operating[0,0] <= started[0,0]","operating[1,0]-started[1,0] <= type1_initial_slack","operating[type,period] <= operating[type,period-1]+started[type,period] for period>0"],"objective":"minimize sum_type,period(base_cost[type]*operating[type,period]+var_cost*power[type,period]+startup_cost[type]*started[type,period])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    base_cost = {
        0: params["base_cost_type0"],
        1: params["base_cost_type1"],
    }
    startup_cost = {
        0: params["startup_cost_type0"],
        1: params["startup_cost_type1"],
    }
    min_output = {
        0: params["min_output_type0"],
        1: params["min_output_type1"],
    }
    max_output = {
        0: params["max_output_type0"],
        1: params["max_output_type1"],
    }
    max_operating = {
        0: params["max_operating_type0"],
        1: params["max_operating_type1"],
    }
    var_cost = params["var_cost"]
    demand = params["demand"]
    reserve_margin = params["reserve_margin"]
    type1_initial_slack = params["type1_initial_slack"]

    model = pyo.ConcreteModel()
    model.generator_types = pyo.Set(initialize=[0, 1], ordered=True)
    model.periods = pyo.RangeSet(0, 3)

    model.operating = pyo.Var(
        model.generator_types,
        model.periods,
        domain=pyo.NonNegativeIntegers,
    )
    model.power = pyo.Var(
        model.generator_types,
        model.periods,
        domain=pyo.NonNegativeReals,
    )
    model.started = pyo.Var(
        model.generator_types,
        model.periods,
        domain=pyo.NonNegativeIntegers,
    )

    def demand_rule(instance, period):
        return sum(
            instance.power[generator_type, period]
            for generator_type in instance.generator_types
        ) >= demand[period]

    model.demand_requirement = pyo.Constraint(
        model.periods, rule=demand_rule
    )

    def minimum_output_rule(instance, generator_type, period):
        return (
            instance.power[generator_type, period]
            >= min_output[generator_type]
            * instance.operating[generator_type, period]
        )

    model.minimum_output_requirement = pyo.Constraint(
        model.generator_types,
        model.periods,
        rule=minimum_output_rule,
    )

    def maximum_output_rule(instance, generator_type, period):
        return (
            instance.power[generator_type, period]
            <= max_output[generator_type]
            * instance.operating[generator_type, period]
        )

    model.maximum_output_requirement = pyo.Constraint(
        model.generator_types,
        model.periods,
        rule=maximum_output_rule,
    )

    def reserve_rule(instance, period):
        return sum(
            max_output[generator_type]
            * instance.operating[generator_type, period]
            for generator_type in instance.generator_types
        ) >= (1 + reserve_margin) * demand[period]

    model.reserve_requirement = pyo.Constraint(
        model.periods, rule=reserve_rule
    )

    def operating_limit_rule(instance, generator_type, period):
        return (
            instance.operating[generator_type, period]
            <= max_operating[generator_type]
        )

    model.operating_limit = pyo.Constraint(
        model.generator_types,
        model.periods,
        rule=operating_limit_rule,
    )

    model.type0_initial_requirement = pyo.Constraint(
        expr=model.operating[0, 0] <= model.started[0, 0]
    )
    model.type1_initial_requirement = pyo.Constraint(
        expr=(
            model.operating[1, 0] - model.started[1, 0]
            <= type1_initial_slack
        )
    )

    def transition_rule(instance, generator_type, period):
        if period == 0:
            return pyo.Constraint.Skip
        return (
            instance.operating[generator_type, period]
            <= instance.operating[generator_type, period - 1]
            + instance.started[generator_type, period]
        )

    model.operating_transition = pyo.Constraint(
        model.generator_types,
        model.periods,
        rule=transition_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            base_cost[generator_type]
            * model.operating[generator_type, period]
            + var_cost * model.power[generator_type, period]
            + startup_cost[generator_type]
            * model.started[generator_type, period]
            for generator_type in model.generator_types
            for period in model.periods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Propagate unrelated runtime errors.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}