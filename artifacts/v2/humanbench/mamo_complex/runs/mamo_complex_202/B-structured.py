# IR: {"sets":{"products":[1,2]},"params":["assembly_hours_type1","testing_hours_type1","material_cost_type1","assembly_hours_type2","testing_hours_type2","material_cost_type2","assembly_capacity","testing_capacity","overtime_max","overtime_cost_per_hour","price_type1","price_type2"],"variables":{"production[products]":"NonNegativeReals","overtime":"NonNegativeReals"},"constraints":["sum(assembly_hours[i]*production[i]) <= assembly_capacity + overtime","sum(testing_hours[i]*production[i]) <= testing_capacity","overtime <= overtime_max"],"objective":"maximize sum((price[i]-material_cost[i])*production[i]) - overtime_cost_per_hour*overtime"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=[1, 2], ordered=True)

    model.assembly_hours = pyo.Param(
        model.products,
        initialize={
            1: params["assembly_hours_type1"],
            2: params["assembly_hours_type2"],
        },
    )
    model.testing_hours = pyo.Param(
        model.products,
        initialize={
            1: params["testing_hours_type1"],
            2: params["testing_hours_type2"],
        },
    )
    model.material_cost = pyo.Param(
        model.products,
        initialize={
            1: params["material_cost_type1"],
            2: params["material_cost_type2"],
        },
    )
    model.price = pyo.Param(
        model.products,
        initialize={
            1: params["price_type1"],
            2: params["price_type2"],
        },
    )
    model.assembly_capacity = pyo.Param(
        initialize=params["assembly_capacity"]
    )
    model.testing_capacity = pyo.Param(
        initialize=params["testing_capacity"]
    )
    model.overtime_max = pyo.Param(
        initialize=params["overtime_max"]
    )
    model.overtime_cost_per_hour = pyo.Param(
        initialize=params["overtime_cost_per_hour"]
    )

    model.production = pyo.Var(
        model.products, domain=pyo.NonNegativeReals
    )
    model.overtime = pyo.Var(domain=pyo.NonNegativeReals)

    model.assembly_limit = pyo.Constraint(
        expr=sum(
            model.assembly_hours[i] * model.production[i]
            for i in model.products
        )
        <= model.assembly_capacity + model.overtime
    )
    model.testing_limit = pyo.Constraint(
        expr=sum(
            model.testing_hours[i] * model.production[i]
            for i in model.products
        )
        <= model.testing_capacity
    )
    model.overtime_limit = pyo.Constraint(
        expr=model.overtime <= model.overtime_max
    )

    model.profit = pyo.Objective(
        expr=sum(
            (model.price[i] - model.material_cost[i])
            * model.production[i]
            for i in model.products
        )
        - model.overtime_cost_per_hour * model.overtime,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}