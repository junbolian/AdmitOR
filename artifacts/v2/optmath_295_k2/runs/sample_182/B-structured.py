# IR: {"sets":{"factories":[0,1,2,3,4,5],"months":[0,1,2,3]},"params":{"min_production":"factory-indexed array or mapping","max_production":"factory-indexed array or mapping","monthly_demand":"month-indexed array or mapping","fixed_cost":"factory-indexed array or mapping; applies each month","variable_cost":"factory-indexed array or mapping; applies each month"},"variables":{"run[f,t]":"Binary","production[f,t]":"NonNegativeReals"},"constraints":["production[f,t] >= min_production[f] * run[f,t] for each factory and month","production[f,t] <= max_production[f] * run[f,t] for each factory and month","sum(production[f,t] for f in factories) >= monthly_demand[t] for each month"],"objective":"minimize sum(fixed_cost[f]*run[f,t] + variable_cost[f]*production[f,t] for each factory and month)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based, factory-indexed and month-indexed inputs."""
    min_production = params["min_production"]
    max_production = params["max_production"]
    monthly_demand = params["monthly_demand"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]

    model = pyo.ConcreteModel()

    model.factories = pyo.RangeSet(0, 5)
    model.months = pyo.RangeSet(0, 3)

    model.minimum_output = pyo.Param(
        model.factories,
        initialize=lambda mdl, factory: min_production[factory],
    )
    model.maximum_output = pyo.Param(
        model.factories,
        initialize=lambda mdl, factory: max_production[factory],
    )
    model.required_output = pyo.Param(
        model.months,
        initialize=lambda mdl, month: monthly_demand[month],
    )
    model.operating_cost = pyo.Param(
        model.factories,
        initialize=lambda mdl, factory: fixed_cost[factory],
    )
    model.unit_cost = pyo.Param(
        model.factories,
        initialize=lambda mdl, factory: variable_cost[factory],
    )

    model.run = pyo.Var(
        model.factories, model.months, domain=pyo.Binary
    )
    model.production = pyo.Var(
        model.factories, model.months, domain=pyo.NonNegativeReals
    )

    def minimum_production_rule(mdl, factory, month):
        return (
            mdl.production[factory, month]
            >= mdl.minimum_output[factory] * mdl.run[factory, month]
        )

    model.minimum_production_constraint = pyo.Constraint(
        model.factories,
        model.months,
        rule=minimum_production_rule,
    )

    def maximum_production_rule(mdl, factory, month):
        return (
            mdl.production[factory, month]
            <= mdl.maximum_output[factory] * mdl.run[factory, month]
        )

    model.maximum_production_constraint = pyo.Constraint(
        model.factories,
        model.months,
        rule=maximum_production_rule,
    )

    def demand_rule(mdl, month):
        return (
            sum(
                mdl.production[factory, month]
                for factory in mdl.factories
            )
            >= mdl.required_output[month]
        )

    model.demand_constraint = pyo.Constraint(
        model.months, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.operating_cost[factory] * model.run[factory, month]
            + model.unit_cost[factory] * model.production[factory, month]
            for factory in model.factories
            for month in model.months
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}