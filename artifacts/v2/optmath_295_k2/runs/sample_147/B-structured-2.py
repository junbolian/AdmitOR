# IR: {"sets":{"G":[0,1],"T":[0,1,2,3]},"params":{"base_cost[g]":["base_cost_type0","base_cost_type1"],"var_cost[g]":["var_cost_type0","var_cost_type1"],"startup_cost[g]":["startup_cost_type0","startup_cost_type1"],"max_units[g]":["max_units_type0","max_units_type1"],"demand[t]":"demand","min_output[g]":["min_output_type0","min_output_type1"],"max_output[g]":["max_output_type0","max_output_type1"],"reserve_margin":"reserve_margin","initial_startup_limit[g]":["max_startup_type0_period0","max_startup_type1_period0"]},"variables":{"operating[g,t]":"nonnegative integer","output[g,t]":"nonnegative real","startups[g,t]":"nonnegative integer"},"constraints":["operating[g,t] <= max_units[g]","sum_g output[g,t] >= demand[t]","output[g,t] >= min_output[g]*operating[g,t]","output[g,t] <= max_output[g]*operating[g,t]","sum_g max_output[g]*operating[g,t] >= (1+reserve_margin)*demand[t]","startups[g,0] = operating[g,0] (initially all units off)","startups[g,0] <= initial_startup_limit[g]","startups[g,t] >= operating[g,t]-operating[g,t-1] for t>0","startups[g,t] <= operating[g,t-1] for t>0","startups[g,t] <= operating[g,t]"],"objective":"minimize sum_g,t(base_cost[g]*operating[g,t]+var_cost[g]*output[g,t]+startup_cost[g]*startups[g,t])"}
import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.generator_types = pyo.Set(initialize=[0, 1], ordered=True)
    model.periods = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)
    model.later_periods = pyo.Set(initialize=[1, 2, 3], ordered=True)

    model.base_cost = pyo.Param(
        model.generator_types,
        initialize={
            0: params["base_cost_type0"],
            1: params["base_cost_type1"],
        },
        within=pyo.NonNegativeReals,
    )
    model.variable_cost = pyo.Param(
        model.generator_types,
        initialize={
            0: params["var_cost_type0"],
            1: params["var_cost_type1"],
        },
        within=pyo.NonNegativeReals,
    )
    model.startup_cost = pyo.Param(
        model.generator_types,
        initialize={
            0: params["startup_cost_type0"],
            1: params["startup_cost_type1"],
        },
        within=pyo.NonNegativeReals,
    )
    model.unit_limit = pyo.Param(
        model.generator_types,
        initialize={
            0: params["max_units_type0"],
            1: params["max_units_type1"],
        },
        within=pyo.NonNegativeIntegers,
    )
    model.power_demand = pyo.Param(
        model.periods,
        initialize={period: params["demand"][period] for period in range(4)},
        within=pyo.NonNegativeReals,
    )
    model.minimum_output = pyo.Param(
        model.generator_types,
        initialize={
            0: params["min_output_type0"],
            1: params["min_output_type1"],
        },
        within=pyo.NonNegativeReals,
    )
    model.maximum_output = pyo.Param(
        model.generator_types,
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
    model.initial_startup_limit = pyo.Param(
        model.generator_types,
        initialize={
            0: params["max_startup_type0_period0"],
            1: params["max_startup_type1_period0"],
        },
        within=pyo.NonNegativeIntegers,
    )

    model.operating = pyo.Var(
        model.generator_types,
        model.periods,
        domain=pyo.NonNegativeIntegers,
    )
    model.output = pyo.Var(
        model.generator_types,
        model.periods,
        domain=pyo.NonNegativeReals,
    )
    model.startups = pyo.Var(
        model.generator_types,
        model.periods,
        domain=pyo.NonNegativeIntegers,
    )

    model.operating_capacity = pyo.Constraint(
        model.generator_types,
        model.periods,
        rule=lambda mdl, gen, period: (
            mdl.operating[gen, period] <= mdl.unit_limit[gen]
        ),
    )
    model.demand_coverage = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: (
            sum(mdl.output[gen, period] for gen in mdl.generator_types)
            >= mdl.power_demand[period]
        ),
    )
    model.minimum_generation = pyo.Constraint(
        model.generator_types,
        model.periods,
        rule=lambda mdl, gen, period: (
            mdl.output[gen, period]
            >= mdl.minimum_output[gen] * mdl.operating[gen, period]
        ),
    )
    model.maximum_generation = pyo.Constraint(
        model.generator_types,
        model.periods,
        rule=lambda mdl, gen, period: (
            mdl.output[gen, period]
            <= mdl.maximum_output[gen] * mdl.operating[gen, period]
        ),
    )
    model.reserve_coverage = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: (
            sum(
                mdl.maximum_output[gen] * mdl.operating[gen, period]
                for gen in mdl.generator_types
            )
            >= (1 + mdl.reserve_margin) * mdl.power_demand[period]
        ),
    )

    # Assume all generators are off immediately before Period 0.
    model.initial_startup_balance = pyo.Constraint(
        model.generator_types,
        rule=lambda mdl, gen: (
            mdl.startups[gen, 0] == mdl.operating[gen, 0]
        ),
    )
    model.initial_startup_capacity = pyo.Constraint(
        model.generator_types,
        rule=lambda mdl, gen: (
            mdl.startups[gen, 0] <= mdl.initial_startup_limit[gen]
        ),
    )
    model.startup_requirement = pyo.Constraint(
        model.generator_types,
        model.later_periods,
        rule=lambda mdl, gen, period: (
            mdl.startups[gen, period]
            >= mdl.operating[gen, period] - mdl.operating[gen, period - 1]
        ),
    )
    model.previous_period_startup_limit = pyo.Constraint(
        model.generator_types,
        model.later_periods,
        rule=lambda mdl, gen, period: (
            mdl.startups[gen, period] <= mdl.operating[gen, period - 1]
        ),
    )
    model.current_period_startup_limit = pyo.Constraint(
        model.generator_types,
        model.periods,
        rule=lambda mdl, gen, period: (
            mdl.startups[gen, period] <= mdl.operating[gen, period]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.base_cost[gen] * model.operating[gen, period]
            + model.variable_cost[gen] * model.output[gen, period]
            + model.startup_cost[gen] * model.startups[gen, period]
            for gen in model.generator_types
            for period in model.periods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except ApplicationError:
        return {"objective": None, "status": "solver_failed"}
    except RuntimeError as exc:
        # APPsi raises this when its default solution loading finds no solution.
        if "no solution can be loaded" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}