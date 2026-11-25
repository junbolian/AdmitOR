# IR: {"sets":{"factories":[0,1,2,3,4,5],"months":[0,1,2,3]},"params":{"min_production":"factory-indexed minimum output","max_production":"factory-indexed capacity","monthly_demand":"month-indexed demand","fixed_cost":"factory-indexed monthly operating cost","variable_cost":"factory-indexed unit production cost"},"variables":{"run[f,t]":"Binary","production[f,t]":"NonNegativeReals"},"constraints":["production[f,t] >= min_production[f] * run[f,t] for every factory and month","production[f,t] <= max_production[f] * run[f,t] for every factory and month","sum(production[f,t] for f in factories) >= monthly_demand[t] for every month"],"objective":"minimize sum(fixed_cost[f]*run[f,t] + variable_cost[f]*production[f,t] for every factory and month)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using factory-indexed input sequences or dictionaries.

    Factory indices are 0 through 5; month indices are 0 through 3.
    Production is continuous.
    """
    min_production = params["min_production"]
    max_production = params["max_production"]
    monthly_demand = params["monthly_demand"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]

    model = pyo.ConcreteModel()

    model.factories = pyo.RangeSet(0, 5)
    model.months = pyo.RangeSet(0, 3)

    model.min_production = pyo.Param(
        model.factories,
        initialize={factory: min_production[factory] for factory in model.factories},
    )
    model.max_production = pyo.Param(
        model.factories,
        initialize={factory: max_production[factory] for factory in model.factories},
    )
    model.monthly_demand = pyo.Param(
        model.months,
        initialize={month: monthly_demand[month] for month in model.months},
    )
    model.fixed_cost = pyo.Param(
        model.factories,
        initialize={factory: fixed_cost[factory] for factory in model.factories},
    )
    model.variable_cost = pyo.Param(
        model.factories,
        initialize={factory: variable_cost[factory] for factory in model.factories},
    )

    model.run = pyo.Var(
        model.factories,
        model.months,
        domain=pyo.Binary,
    )
    model.production = pyo.Var(
        model.factories,
        model.months,
        domain=pyo.NonNegativeReals,
    )

    def minimum_production_rule(mdl, factory, month):
        return (
            mdl.production[factory, month]
            >= mdl.min_production[factory] * mdl.run[factory, month]
        )

    model.minimum_production_constraint = pyo.Constraint(
        model.factories,
        model.months,
        rule=minimum_production_rule,
    )

    def maximum_production_rule(mdl, factory, month):
        return (
            mdl.production[factory, month]
            <= mdl.max_production[factory] * mdl.run[factory, month]
        )

    model.maximum_production_constraint = pyo.Constraint(
        model.factories,
        model.months,
        rule=maximum_production_rule,
    )

    def demand_rule(mdl, month):
        return (
            sum(mdl.production[factory, month] for factory in mdl.factories)
            >= mdl.monthly_demand[month]
        )

    model.demand_constraint = pyo.Constraint(
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
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}