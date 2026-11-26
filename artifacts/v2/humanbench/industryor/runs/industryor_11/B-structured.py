# IR: {"sets":{"products":["advanced","intermediate","basic"]},"params":["labor_hours_advanced","inspection_hours_advanced","profit_advanced","labor_hours_intermediate","inspection_hours_intermediate","profit_intermediate","labor_hours_basic","inspection_hours_basic","profit_basic","labor_capacity","inspection_capacity","demand_advanced","demand_intermediate","demand_basic"],"variables":{"production[product]":"nonnegative integer"},"constraints":["sum(labor_hours[product]*production[product]) <= labor_capacity","sum(inspection_hours[product]*production[product]) <= inspection_capacity","production[product] <= demand[product] for each product"],"objective":"maximize sum(profit[product]*production[product])"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(
        initialize=["advanced", "intermediate", "basic"],
        ordered=True,
    )

    model.labor_hours = pyo.Param(
        model.products,
        initialize={
            "advanced": params["labor_hours_advanced"],
            "intermediate": params["labor_hours_intermediate"],
            "basic": params["labor_hours_basic"],
        },
    )
    model.inspection_hours = pyo.Param(
        model.products,
        initialize={
            "advanced": params["inspection_hours_advanced"],
            "intermediate": params["inspection_hours_intermediate"],
            "basic": params["inspection_hours_basic"],
        },
    )
    model.unit_profit = pyo.Param(
        model.products,
        initialize={
            "advanced": params["profit_advanced"],
            "intermediate": params["profit_intermediate"],
            "basic": params["profit_basic"],
        },
    )
    model.demand_limit = pyo.Param(
        model.products,
        initialize={
            "advanced": params["demand_advanced"],
            "intermediate": params["demand_intermediate"],
            "basic": params["demand_basic"],
        },
    )
    model.labor_capacity = pyo.Param(initialize=params["labor_capacity"])
    model.inspection_capacity = pyo.Param(
        initialize=params["inspection_capacity"]
    )

    model.production = pyo.Var(
        model.products,
        domain=pyo.NonNegativeIntegers,
    )

    model.labor_limit = pyo.Constraint(
        expr=sum(
            model.labor_hours[product] * model.production[product]
            for product in model.products
        )
        <= model.labor_capacity
    )
    model.inspection_limit = pyo.Constraint(
        expr=sum(
            model.inspection_hours[product] * model.production[product]
            for product in model.products
        )
        <= model.inspection_capacity
    )

    def demand_rule(instance, product):
        return instance.production[product] <= instance.demand_limit[product]

    model.demand_constraints = pyo.Constraint(
        model.products,
        rule=demand_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[product] * model.production[product]
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}