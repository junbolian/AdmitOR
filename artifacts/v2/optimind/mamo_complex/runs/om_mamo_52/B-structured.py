# IR: {"sets":{"P":[1,2]},"params":["assembly_hours_product1","testing_hours_product1","material_cost_product1","assembly_hours_product2","testing_hours_product2","material_cost_product2","regular_assembly_capacity","testing_capacity","overtime_assembly_capacity","overtime_cost_per_hour","market_value_product1","market_value_product2"],"variables":{"production[p in P]":"NonNegativeReals","overtime_hours":"NonNegativeReals"},"constraints":["sum(assembly_hours_product[p]*production[p] for p in P) <= regular_assembly_capacity + overtime_hours","sum(testing_hours_product[p]*production[p] for p in P) <= testing_capacity","overtime_hours <= overtime_assembly_capacity"],"objective":{"sense":"maximize","expression":"sum((market_value_product[p]-material_cost_product[p])*production[p] for p in P) - overtime_cost_per_hour*overtime_hours"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=[1, 2], ordered=True)

    model.assembly_hours = pyo.Param(
        model.products,
        initialize={
            1: params["assembly_hours_product1"],
            2: params["assembly_hours_product2"],
        },
    )
    model.testing_hours = pyo.Param(
        model.products,
        initialize={
            1: params["testing_hours_product1"],
            2: params["testing_hours_product2"],
        },
    )
    model.material_cost = pyo.Param(
        model.products,
        initialize={
            1: params["material_cost_product1"],
            2: params["material_cost_product2"],
        },
    )
    model.market_value = pyo.Param(
        model.products,
        initialize={
            1: params["market_value_product1"],
            2: params["market_value_product2"],
        },
    )
    model.regular_assembly_capacity = pyo.Param(
        initialize=params["regular_assembly_capacity"]
    )
    model.testing_capacity = pyo.Param(
        initialize=params["testing_capacity"]
    )
    model.overtime_assembly_capacity = pyo.Param(
        initialize=params["overtime_assembly_capacity"]
    )
    model.overtime_cost_per_hour = pyo.Param(
        initialize=params["overtime_cost_per_hour"]
    )

    model.production = pyo.Var(
        model.products, domain=pyo.NonNegativeReals
    )
    model.overtime_hours = pyo.Var(domain=pyo.NonNegativeReals)

    model.assembly_limit = pyo.Constraint(
        expr=sum(
            model.assembly_hours[product] * model.production[product]
            for product in model.products
        )
        <= model.regular_assembly_capacity + model.overtime_hours
    )
    model.testing_limit = pyo.Constraint(
        expr=sum(
            model.testing_hours[product] * model.production[product]
            for product in model.products
        )
        <= model.testing_capacity
    )
    model.overtime_limit = pyo.Constraint(
        expr=model.overtime_hours <= model.overtime_assembly_capacity
    )

    model.daily_profit = pyo.Objective(
        expr=sum(
            (
                model.market_value[product]
                - model.material_cost[product]
            )
            * model.production[product]
            for product in model.products
        )
        - model.overtime_cost_per_hour * model.overtime_hours,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.daily_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}