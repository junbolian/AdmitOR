# IR: {"sets":{"factories":[0,1,2,3,4,5],"months":[0,1,2,3,4]},"params":{"fixed_cost":"factories -> real","variable_cost":"factories -> real","min_production":"factories -> nonnegative real","max_production":"factories -> nonnegative real","demand":"months -> nonnegative real"},"variables":{"run[factory,month]":"binary","production[factory,month]":"nonnegative continuous"},"constraints":["production[factory,month] >= min_production[factory] * run[factory,month] for each factory,month","production[factory,month] <= max_production[factory] * run[factory,month] for each factory,month","sum(production[factory,month] for factory in factories) >= demand[month] for each month"],"objective":"minimize sum(fixed_cost[factory]*run[factory,month] + variable_cost[factory]*production[factory,month] for each factory,month)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.factories = pyo.RangeSet(0, 5)
    model.months = pyo.RangeSet(0, 4)

    model.fixed_cost = pyo.Param(
        model.factories,
        initialize={
            factory: params["fixed_cost"][factory]
            for factory in model.factories
        },
        within=pyo.Reals,
    )
    model.variable_cost = pyo.Param(
        model.factories,
        initialize={
            factory: params["variable_cost"][factory]
            for factory in model.factories
        },
        within=pyo.Reals,
    )
    model.min_production = pyo.Param(
        model.factories,
        initialize={
            factory: params["min_production"][factory]
            for factory in model.factories
        },
        within=pyo.NonNegativeReals,
    )
    model.max_production = pyo.Param(
        model.factories,
        initialize={
            factory: params["max_production"][factory]
            for factory in model.factories
        },
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.months,
        initialize={
            month: params["demand"][month]
            for month in model.months
        },
        within=pyo.NonNegativeReals,
    )

    model.run = pyo.Var(
        model.factories, model.months, domain=pyo.Binary
    )
    model.production = pyo.Var(
        model.factories, model.months, domain=pyo.NonNegativeReals
    )

    def minimum_production_rule(instance, factory, month):
        return (
            instance.production[factory, month]
            >= instance.min_production[factory]
            * instance.run[factory, month]
        )

    def maximum_production_rule(instance, factory, month):
        return (
            instance.production[factory, month]
            <= instance.max_production[factory]
            * instance.run[factory, month]
        )

    def demand_rule(instance, month):
        return (
            sum(
                instance.production[factory, month]
                for factory in instance.factories
            )
            >= instance.demand[month]
        )

    model.minimum_production_constraints = pyo.Constraint(
        model.factories,
        model.months,
        rule=minimum_production_rule,
    )
    model.maximum_production_constraints = pyo.Constraint(
        model.factories,
        model.months,
        rule=maximum_production_rule,
    )
    model.demand_constraints = pyo.Constraint(
        model.months,
        rule=demand_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[factory] * model.run[factory, month]
            + model.variable_cost[factory] * model.production[factory, month]
            for factory in model.factories
            for month in model.months
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" not in str(exc).lower():
            raise
        # No solution was loaded; objective retrieval determines success.

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}