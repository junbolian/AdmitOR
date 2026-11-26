# IR: {"sets":{"products":["recorder","radio"]},"params":["labor_cost_recorder","labor_cost_radio","material_cost_recorder","material_cost_radio","price_recorder","price_radio","raw_material_capacity_recorder","raw_material_capacity_radio","cash_initial","accounts_receivable_initial","inventory_initial","loan_liability","ar_collection_december","loan_payment_december","rent_december","new_material_january","min_cash_january","min_current_ratio"],"variables":{"production[products]":"NonNegativeReals"},"expressions":{"cash_january":"cash_initial + ar_collection_december - loan_payment_december - rent_december - sum(labor_cost[p]*production[p])","receivables_january":"accounts_receivable_initial - ar_collection_december + sum(price[p]*production[p])","inventory_january":"inventory_initial - sum(material_cost[p]*production[p]) + new_material_january","liabilities_january":"loan_liability - loan_payment_december + new_material_january"},"constraints":["production[p] <= raw_material_capacity[p] for each product p","cash_january >= min_cash_january","cash_january + receivables_january + inventory_january >= min_current_ratio * liabilities_january"],"objective":{"sense":"maximize","expression":"sum((price[p] - labor_cost[p] - material_cost[p])*production[p])"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(
        initialize=["recorder", "radio"], ordered=True
    )

    model.labor_cost = pyo.Param(
        model.products,
        initialize={
            "recorder": params["labor_cost_recorder"],
            "radio": params["labor_cost_radio"],
        },
    )
    model.material_cost = pyo.Param(
        model.products,
        initialize={
            "recorder": params["material_cost_recorder"],
            "radio": params["material_cost_radio"],
        },
    )
    model.price = pyo.Param(
        model.products,
        initialize={
            "recorder": params["price_recorder"],
            "radio": params["price_radio"],
        },
    )
    model.raw_material_capacity = pyo.Param(
        model.products,
        initialize={
            "recorder": params["raw_material_capacity_recorder"],
            "radio": params["raw_material_capacity_radio"],
        },
    )

    financial_names = (
        "cash_initial",
        "accounts_receivable_initial",
        "inventory_initial",
        "loan_liability",
        "ar_collection_december",
        "loan_payment_december",
        "rent_december",
        "new_material_january",
        "min_cash_january",
        "min_current_ratio",
    )
    model.financial = pyo.Param(
        financial_names,
        initialize={key: params[key] for key in financial_names},
    )

    # Production quantities are continuous, as in a linear programming model.
    model.production = pyo.Var(
        model.products, domain=pyo.NonNegativeReals
    )

    # Existing raw materials require no December cash payment.
    # December credit sales produce receivables, not December cash.
    model.cash_january = pyo.Expression(
        expr=(
            model.financial["cash_initial"]
            + model.financial["ar_collection_december"]
            - model.financial["loan_payment_december"]
            - model.financial["rent_december"]
            - sum(
                model.labor_cost[product] * model.production[product]
                for product in model.products
            )
        )
    )

    model.receivables_january = pyo.Expression(
        expr=(
            model.financial["accounts_receivable_initial"]
            - model.financial["ar_collection_december"]
            + sum(
                model.price[product] * model.production[product]
                for product in model.products
            )
        )
    )

    model.inventory_january = pyo.Expression(
        expr=(
            model.financial["inventory_initial"]
            - sum(
                model.material_cost[product] * model.production[product]
                for product in model.products
            )
            + model.financial["new_material_january"]
        )
    )

    # January materials increase both inventory and accounts payable.
    model.liabilities_january = pyo.Expression(
        expr=(
            model.financial["loan_liability"]
            - model.financial["loan_payment_december"]
            + model.financial["new_material_january"]
        )
    )

    def capacity_rule(instance, product):
        return (
            instance.production[product]
            <= instance.raw_material_capacity[product]
        )

    model.material_capacity_limit = pyo.Constraint(
        model.products, rule=capacity_rule
    )

    model.minimum_cash_requirement = pyo.Constraint(
        expr=(
            model.cash_january
            >= model.financial["min_cash_january"]
        )
    )

    model.current_ratio_requirement = pyo.Constraint(
        expr=(
            model.cash_january
            + model.receivables_january
            + model.inventory_january
            >= model.financial["min_current_ratio"]
            * model.liabilities_january
        )
    )

    # Fixed rent affects cash but is not a production contribution cost.
    model.profit_contribution = pyo.Objective(
        expr=sum(
            (
                model.price[product]
                - model.labor_cost[product]
                - model.material_cost[product]
            )
            * model.production[product]
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.profit_contribution))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}