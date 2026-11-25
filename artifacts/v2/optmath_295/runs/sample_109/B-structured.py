# IR: {"sets":{"G":[0,1,2],"T":[0,1,2,3,4]},"params":{"base_cost":"G","per_mw_cost":"G","startup_cost":"G","demand":"T","reserve_demand":"T","min_output":"G","max_output":"G","max_generators":"G","initial_startup_allowance":"G"},"variables":{"generators[g,t]":"nonnegative integer","power[g,t]":"nonnegative real","startups[g,t]":"nonnegative integer"},"constraints":["forall t: sum_g power[g,t] >= demand[t]","forall g,t: power[g,t] >= min_output[g]*generators[g,t]","forall g,t: power[g,t] <= max_output[g]*generators[g,t]","forall g,t: generators[g,t] <= max_generators[g]","forall t: sum_g max_output[g]*generators[g,t] >= reserve_demand[t]","forall g: generators[g,0] <= startups[g,0]+initial_startup_allowance[g]","forall g,t>0: generators[g,t] <= generators[g,t-1]+startups[g,t]"],"objective":"minimize sum_g,t (base_cost[g]*generators[g,t]+per_mw_cost[g]*power[g,t]+startup_cost[g]*startups[g,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.G = pyo.RangeSet(0, 2)
    model.T = pyo.RangeSet(0, 4)

    model.base_cost = pyo.Param(
        model.G, initialize=lambda mdl, g: params["base_cost"][g]
    )
    model.per_mw_cost = pyo.Param(
        model.G, initialize=lambda mdl, g: params["per_mw_cost"][g]
    )
    model.startup_cost = pyo.Param(
        model.G, initialize=lambda mdl, g: params["startup_cost"][g]
    )
    model.demand = pyo.Param(
        model.T, initialize=lambda mdl, t: params["demand"][t]
    )
    model.reserve_demand = pyo.Param(
        model.T, initialize=lambda mdl, t: params["reserve_demand"][t]
    )
    model.min_output = pyo.Param(
        model.G, initialize=lambda mdl, g: params["min_output"][g]
    )
    model.max_output = pyo.Param(
        model.G, initialize=lambda mdl, g: params["max_output"][g]
    )
    model.max_generators = pyo.Param(
        model.G, initialize=lambda mdl, g: params["max_generators"][g]
    )
    model.initial_startup_allowance = pyo.Param(
        model.G,
        initialize=lambda mdl, g: params["initial_startup_allowance"][g],
    )

    model.generators = pyo.Var(model.G, model.T, domain=pyo.NonNegativeIntegers)
    model.power = pyo.Var(model.G, model.T, domain=pyo.NonNegativeReals)
    model.startups = pyo.Var(model.G, model.T, domain=pyo.NonNegativeIntegers)

    model.demand_requirement = pyo.Constraint(
        model.T,
        rule=lambda mdl, t: (
            sum(mdl.power[g, t] for g in mdl.G) >= mdl.demand[t]
        ),
    )

    model.minimum_output_requirement = pyo.Constraint(
        model.G,
        model.T,
        rule=lambda mdl, g, t: (
            mdl.power[g, t] >= mdl.min_output[g] * mdl.generators[g, t]
        ),
    )

    model.maximum_output_requirement = pyo.Constraint(
        model.G,
        model.T,
        rule=lambda mdl, g, t: (
            mdl.power[g, t] <= mdl.max_output[g] * mdl.generators[g, t]
        ),
    )

    model.generator_availability = pyo.Constraint(
        model.G,
        model.T,
        rule=lambda mdl, g, t: (
            mdl.generators[g, t] <= mdl.max_generators[g]
        ),
    )

    model.reserve_requirement = pyo.Constraint(
        model.T,
        rule=lambda mdl, t: (
            sum(mdl.max_output[g] * mdl.generators[g, t] for g in mdl.G)
            >= mdl.reserve_demand[t]
        ),
    )

    model.initial_startup_requirement = pyo.Constraint(
        model.G,
        rule=lambda mdl, g: (
            mdl.generators[g, 0]
            <= mdl.startups[g, 0] + mdl.initial_startup_allowance[g]
        ),
    )

    def subsequent_startup_rule(mdl, g, t):
        if t == 0:
            return pyo.Constraint.Skip
        return (
            mdl.generators[g, t]
            <= mdl.generators[g, t - 1] + mdl.startups[g, t]
        )

    model.subsequent_startup_requirement = pyo.Constraint(
        model.G, model.T, rule=subsequent_startup_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.base_cost[g] * model.generators[g, t]
            + model.per_mw_cost[g] * model.power[g, t]
            + model.startup_cost[g] * model.startups[g, t]
            for g in model.G
            for t in model.T
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # HiGHS raises this when its default solution loading finds no solution.
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}