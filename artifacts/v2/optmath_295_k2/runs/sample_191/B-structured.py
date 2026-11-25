# IR: {"sets":{"factories":[0,1,2,3,4,5],"months":[0,1,2,3,4]},"params":{"fixed_cost":"real[factory]","variable_cost":"real[factory]","min_production":"real[factory]","max_production":"real[factory]","demand":"real[month]"},"variables":{"run":"binary[factory,month]","production":"nonnegative continuous[factory,month]"},"constraints":["production[f,t] >= min_production[f]*run[f,t] for each factory f and month t","production[f,t] <= max_production[f]*run[f,t] for each factory f and month t","sum(production[f,t] for f in factories) >= demand[t] for each month t"],"objective":{"sense":"minimize","expression":"sum(fixed_cost[f]*run[f,t] + variable_cost[f]*production[f,t] for f in factories for t in months)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.factories = pyo.RangeSet(0, 5)
    model.months = pyo.RangeSet(0, 4)

    model.fixed_cost = pyo.Param(
        model.factories,
        initialize={f: params["fixed_cost"][f] for f in model.factories},
        within=pyo.Reals,
    )
    model.variable_cost = pyo.Param(
        model.factories,
        initialize={f: params["variable_cost"][f] for f in model.factories},
        within=pyo.Reals,
    )
    model.min_production = pyo.Param(
        model.factories,
        initialize={f: params["min_production"][f] for f in model.factories},
        within=pyo.Reals,
    )
    model.max_production = pyo.Param(
        model.factories,
        initialize={f: params["max_production"][f] for f in model.factories},
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.months,
        initialize={t: params["demand"][t] for t in model.months},
        within=pyo.Reals,
    )

    model.run = pyo.Var(model.factories, model.months, domain=pyo.Binary)
    model.production = pyo.Var(
        model.factories, model.months, domain=pyo.NonNegativeReals
    )

    model.minimum_output = pyo.Constraint(
        model.factories,
        model.months,
        rule=lambda mdl, f, t: (
            mdl.production[f, t] >= mdl.min_production[f] * mdl.run[f, t]
        ),
    )
    model.maximum_output = pyo.Constraint(
        model.factories,
        model.months,
        rule=lambda mdl, f, t: (
            mdl.production[f, t] <= mdl.max_production[f] * mdl.run[f, t]
        ),
    )
    model.demand_satisfaction = pyo.Constraint(
        model.months,
        rule=lambda mdl, t: (
            sum(mdl.production[f, t] for f in mdl.factories) >= mdl.demand[t]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[f] * model.run[f, t]
            + model.variable_cost[f] * model.production[f, t]
            for f in model.factories
            for t in model.months
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # APPsi raises this when no feasible solution can be loaded.
        # Let unrelated, unexpected runtime errors propagate.
        if "A feasible solution was not found" not in str(error):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}