# IR: {"sets":{"properties":[1,2,3,4]},"params":{"income":"annual income indexed by property","cost":"purchase cost indexed by property","budget":"total available budget"},"variables":{"buy[property]":"binary"},"constraints":["sum(cost[property]*buy[property] for property in properties) <= budget","buy[4] + buy[3] <= 1"],"objective":"maximize sum(income[property]*buy[property] for property in properties)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept income/cost as four-element sequences or mappings keyed 1 through 4."""
    income = params["income"]
    cost = params["cost"]
    budget = params["budget"]

    def property_value(values, property_id):
        if isinstance(values, Mapping):
            return values[property_id]
        return values[property_id - 1]

    model = pyo.ConcreteModel()
    model.properties = pyo.RangeSet(1, 4)

    model.annual_income = pyo.Param(
        model.properties,
        initialize={
            property_id: property_value(income, property_id)
            for property_id in model.properties
        },
    )
    model.purchase_cost = pyo.Param(
        model.properties,
        initialize={
            property_id: property_value(cost, property_id)
            for property_id in model.properties
        },
    )
    model.available_budget = pyo.Param(initialize=budget)

    model.buy = pyo.Var(model.properties, domain=pyo.Binary)

    model.budget_limit = pyo.Constraint(
        expr=sum(
            model.purchase_cost[property_id] * model.buy[property_id]
            for property_id in model.properties
        )
        <= model.available_budget
    )
    model.property_exclusion = pyo.Constraint(
        expr=model.buy[4] + model.buy[3] <= 1
    )

    model.total_annual_income = pyo.Objective(
        expr=sum(
            model.annual_income[property_id] * model.buy[property_id]
            for property_id in model.properties
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_annual_income))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}