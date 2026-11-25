# IR: {"sets":{"types":[0,1,2],"periods":[0,1,2,3,4]},"params":{"base_cost":"types -> real","marginal_cost":"types -> real","startup_cost":"types -> real","demand":"periods -> real","min_output":"types -> real","max_output":"types -> real","max_generators":"types -> nonnegative integer, immutable","reserve_requirement":"periods -> real","initial_startup_bound":"types -> real"},"variables":{"generators[type,period]":"nonnegative integer","output[type,period]":"nonnegative real","startups[type,period]":"nonnegative integer"},"constraints":["For each period: sum_type output[type,period] >= demand[period]","For each type,period: output[type,period] >= min_output[type]*generators[type,period]","For each type,period: output[type,period] <= max_output[type]*generators[type,period]","For each type,period: generators[type,period] <= max_generators[type]","For each period: sum_type max_output[type]*generators[type,period] >= reserve_requirement[period]","For each type: generators[type,0] <= startups[type,0] + initial_startup_bound[type]","For each type,period>0: generators[type,period] <= generators[type,period-1] + startups[type,period]"],"objective":"minimize sum_type,period(base_cost[type]*generators[type,period] + marginal_cost[type]*output[type,period] + startup_cost[type]*startups[type,period])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.generator_types = pyo.RangeSet(0, 2)
    model.periods = pyo.RangeSet(0, 4)

    model.base_cost = pyo.Param(
        model.generator_types,
        initialize={
            kind: params["base_cost"][kind]
            for kind in model.generator_types
        },
        within=pyo.Reals,
        mutable=False,
    )
    model.marginal_cost = pyo.Param(
        model.generator_types,
        initialize={
            kind: params["marginal_cost"][kind]
            for kind in model.generator_types
        },
        within=pyo.Reals,
        mutable=False,
    )
    model.startup_cost = pyo.Param(
        model.generator_types,
        initialize={
            kind: params["startup_cost"][kind]
            for kind in model.generator_types
        },
        within=pyo.Reals,
        mutable=False,
    )
    model.demand = pyo.Param(
        model.periods,
        initialize={
            period: params["demand"][period]
            for period in model.periods
        },
        within=pyo.Reals,
        mutable=False,
    )
    model.min_output = pyo.Param(
        model.generator_types,
        initialize={
            kind: params["min_output"][kind]
            for kind in model.generator_types
        },
        within=pyo.Reals,
        mutable=False,
    )
    model.max_output = pyo.Param(
        model.generator_types,
        initialize={
            kind: params["max_output"][kind]
            for kind in model.generator_types
        },
        within=pyo.Reals,
        mutable=False,
    )
    model.max_generators = pyo.Param(
        model.generator_types,
        initialize={
            kind: params["max_generators"][kind]
            for kind in model.generator_types
        },
        within=pyo.NonNegativeIntegers,
        mutable=False,
    )
    model.reserve_requirement = pyo.Param(
        model.periods,
        initialize={
            period: params["reserve_requirement"][period]
            for period in model.periods
        },
        within=pyo.Reals,
        mutable=False,
    )
    model.initial_startup_bound = pyo.Param(
        model.generator_types,
        initialize={
            kind: params["initial_startup_bound"][kind]
            for kind in model.generator_types
        },
        within=pyo.Reals,
        mutable=False,
    )

    model.generators = pyo.Var(
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

    def demand_rule(model, period):
        return (
            sum(model.output[kind, period] for kind in model.generator_types)
            >= model.demand[period]
        )

    model.demand_constraints = pyo.Constraint(
        model.periods, rule=demand_rule
    )

    def minimum_output_rule(model, kind, period):
        return (
            model.output[kind, period]
            >= model.min_output[kind] * model.generators[kind, period]
        )

    model.minimum_output_constraints = pyo.Constraint(
        model.generator_types,
        model.periods,
        rule=minimum_output_rule,
    )

    def maximum_output_rule(model, kind, period):
        return (
            model.output[kind, period]
            <= model.max_output[kind] * model.generators[kind, period]
        )

    model.maximum_output_constraints = pyo.Constraint(
        model.generator_types,
        model.periods,
        rule=maximum_output_rule,
    )

    def availability_rule(model, kind, period):
        return (
            model.generators[kind, period]
            <= model.max_generators[kind]
        )

    model.availability_constraints = pyo.Constraint(
        model.generator_types,
        model.periods,
        rule=availability_rule,
    )

    def reserve_rule(model, period):
        return (
            sum(
                model.max_output[kind] * model.generators[kind, period]
                for kind in model.generator_types
            )
            >= model.reserve_requirement[period]
        )

    model.reserve_constraints = pyo.Constraint(
        model.periods, rule=reserve_rule
    )

    def startup_rule(model, kind, period):
        if period == 0:
            return (
                model.generators[kind, period]
                <= model.startups[kind, period]
                + model.initial_startup_bound[kind]
            )
        return (
            model.generators[kind, period]
            <= model.generators[kind, period - 1]
            + model.startups[kind, period]
        )

    model.startup_constraints = pyo.Constraint(
        model.generator_types,
        model.periods,
        rule=startup_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.base_cost[kind] * model.generators[kind, period]
            + model.marginal_cost[kind] * model.output[kind, period]
            + model.startup_cost[kind] * model.startups[kind, period]
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