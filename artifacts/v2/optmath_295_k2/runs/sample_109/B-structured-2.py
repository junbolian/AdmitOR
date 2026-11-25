# IR: {"sets":{"G":[0,1,2],"T":[0,1,2,3,4]},"params":{"base_cost":"G -> real","marginal_cost":"G -> real","startup_cost":"G -> real","demand":"T -> real","min_output":"G -> real","max_output":"G -> real","max_generators":"G -> nonnegative integer, immutable","reserve_requirement":"T -> real","initial_startup_bound":"G -> real"},"variables":{"generators[g,t]":"nonnegative integer","output[g,t]":"nonnegative real","startups[g,t]":"nonnegative integer"},"constraints":["sum_g output[g,t] >= demand[t] for t in T","output[g,t] >= min_output[g]*generators[g,t] for g in G,t in T","output[g,t] <= max_output[g]*generators[g,t] for g in G,t in T","generators[g,t] <= max_generators[g] for g in G,t in T","sum_g max_output[g]*generators[g,t] >= reserve_requirement[t] for t in T","generators[g,0] <= startups[g,0]+initial_startup_bound[g] for g in G","generators[g,t] <= generators[g,t-1]+startups[g,t] for g in G,t in T with t>0"],"objective":"minimize sum_{g,t}(base_cost[g]*generators[g,t]+marginal_cost[g]*output[g,t]+startup_cost[g]*startups[g,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.G = pyo.RangeSet(0, 2)
    model.T = pyo.RangeSet(0, 4)

    model.base_cost = pyo.Param(
        model.G,
        initialize=lambda mdl, g: params["base_cost"][g],
        within=pyo.Reals,
        mutable=False,
    )
    model.marginal_cost = pyo.Param(
        model.G,
        initialize=lambda mdl, g: params["marginal_cost"][g],
        within=pyo.Reals,
        mutable=False,
    )
    model.startup_cost = pyo.Param(
        model.G,
        initialize=lambda mdl, g: params["startup_cost"][g],
        within=pyo.Reals,
        mutable=False,
    )
    model.demand = pyo.Param(
        model.T,
        initialize=lambda mdl, t: params["demand"][t],
        within=pyo.Reals,
        mutable=False,
    )
    model.min_output = pyo.Param(
        model.G,
        initialize=lambda mdl, g: params["min_output"][g],
        within=pyo.Reals,
        mutable=False,
    )
    model.max_output = pyo.Param(
        model.G,
        initialize=lambda mdl, g: params["max_output"][g],
        within=pyo.Reals,
        mutable=False,
    )
    model.max_generators = pyo.Param(
        model.G,
        initialize=lambda mdl, g: params["max_generators"][g],
        within=pyo.NonNegativeIntegers,
        mutable=False,
    )
    model.reserve_requirement = pyo.Param(
        model.T,
        initialize=lambda mdl, t: params["reserve_requirement"][t],
        within=pyo.Reals,
        mutable=False,
    )
    model.initial_startup_bound = pyo.Param(
        model.G,
        initialize=lambda mdl, g: params["initial_startup_bound"][g],
        within=pyo.Reals,
        mutable=False,
    )

    model.generators = pyo.Var(
        model.G, model.T, domain=pyo.NonNegativeIntegers
    )
    model.output = pyo.Var(
        model.G, model.T, domain=pyo.NonNegativeReals
    )
    model.startups = pyo.Var(
        model.G, model.T, domain=pyo.NonNegativeIntegers
    )

    model.demand_constraint = pyo.Constraint(
        model.T,
        rule=lambda mdl, t: (
            sum(mdl.output[g, t] for g in mdl.G) >= mdl.demand[t]
        ),
    )

    model.minimum_output_constraint = pyo.Constraint(
        model.G,
        model.T,
        rule=lambda mdl, g, t: (
            mdl.output[g, t] >= mdl.min_output[g] * mdl.generators[g, t]
        ),
    )

    model.maximum_output_constraint = pyo.Constraint(
        model.G,
        model.T,
        rule=lambda mdl, g, t: (
            mdl.output[g, t] <= mdl.max_output[g] * mdl.generators[g, t]
        ),
    )

    model.availability_constraint = pyo.Constraint(
        model.G,
        model.T,
        rule=lambda mdl, g, t: (
            mdl.generators[g, t] <= mdl.max_generators[g]
        ),
    )

    model.reserve_constraint = pyo.Constraint(
        model.T,
        rule=lambda mdl, t: (
            sum(
                mdl.max_output[g] * mdl.generators[g, t]
                for g in mdl.G
            )
            >= mdl.reserve_requirement[t]
        ),
    )

    model.initial_startup_constraint = pyo.Constraint(
        model.G,
        rule=lambda mdl, g: (
            mdl.generators[g, 0]
            <= mdl.startups[g, 0] + mdl.initial_startup_bound[g]
        ),
    )

    def subsequent_startup_rule(mdl, g, t):
        if t == 0:
            return pyo.Constraint.Skip
        return (
            mdl.generators[g, t]
            <= mdl.generators[g, t - 1] + mdl.startups[g, t]
        )

    model.subsequent_startup_constraint = pyo.Constraint(
        model.G, model.T, rule=subsequent_startup_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.base_cost[g] * model.generators[g, t]
            + model.marginal_cost[g] * model.output[g, t]
            + model.startup_cost[g] * model.startups[g, t]
            for g in model.G
            for t in model.T
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