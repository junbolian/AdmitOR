# IR: {"sets":{"factories":[0,1,2,3,4],"months":[0,1,2,3]},"params":{"fixed_cost":"factory-indexed","var_cost":"factory-indexed","min_prod":"factory-indexed","max_prod":"factory-indexed","demand":"month-indexed"},"variables":{"operating[f,t]":"Binary","production[f,t]":"NonNegativeReals"},"constraints":["production[f,t] >= min_prod[f] * operating[f,t] for all f,t","production[f,t] <= max_prod[f] * operating[f,t] for all f,t","sum_f production[f,t] >= demand[t] for all t"],"objective":"minimize sum_f,t (fixed_cost[f] * operating[f,t] + var_cost[f] * production[f,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.factories = pyo.RangeSet(0, 4)
    model.months = pyo.RangeSet(0, 3)

    model.fixed_cost = pyo.Param(
        model.factories,
        initialize=lambda mdl, factory: params["fixed_cost"][factory],
    )
    model.var_cost = pyo.Param(
        model.factories,
        initialize=lambda mdl, factory: params["var_cost"][factory],
    )
    model.min_prod = pyo.Param(
        model.factories,
        initialize=lambda mdl, factory: params["min_prod"][factory],
    )
    model.max_prod = pyo.Param(
        model.factories,
        initialize=lambda mdl, factory: params["max_prod"][factory],
    )
    model.demand = pyo.Param(
        model.months,
        initialize=lambda mdl, month: params["demand"][month],
    )

    model.operating = pyo.Var(
        model.factories, model.months, domain=pyo.Binary
    )
    model.production = pyo.Var(
        model.factories, model.months, domain=pyo.NonNegativeReals
    )

    model.minimum_production = pyo.Constraint(
        model.factories,
        model.months,
        rule=lambda mdl, factory, month: (
            mdl.production[factory, month]
            >= mdl.min_prod[factory] * mdl.operating[factory, month]
        ),
    )

    model.maximum_production = pyo.Constraint(
        model.factories,
        model.months,
        rule=lambda mdl, factory, month: (
            mdl.production[factory, month]
            <= mdl.max_prod[factory] * mdl.operating[factory, month]
        ),
    )

    model.demand_satisfaction = pyo.Constraint(
        model.months,
        rule=lambda mdl, month: (
            sum(
                mdl.production[factory, month]
                for factory in mdl.factories
            )
            >= mdl.demand[month]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[factory] * model.operating[factory, month]
            + model.var_cost[factory] * model.production[factory, month]
            for factory in model.factories
            for month in model.months
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Objective retrieval below remains the sole success test.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}