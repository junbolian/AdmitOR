# IR: {"sets":["products={tape,radio}"],"params":["labor_cost_tape","labor_cost_radio","material_cost_tape","material_cost_radio","price_tape","price_radio","raw_material_capacity_tape","raw_material_capacity_radio","cash_initial","accounts_receivable_initial","inventory_initial","bank_loan_initial","ar_collection_december","loan_repayment_december","rent_december","raw_material_received_january","min_cash_january","min_current_ratio_january"],"variables":{"production[tape]":"NonNegativeReals","production[radio]":"NonNegativeReals"},"expressions":{"labor":"sum(labor_cost[p]*production[p])","materials_used":"sum(material_cost[p]*production[p])","sales":"sum(price[p]*production[p])","cash_january":"cash_initial+ar_collection_december-loan_repayment_december-rent_december-labor","receivables_january":"accounts_receivable_initial-ar_collection_december+sales","inventory_january":"inventory_initial-materials_used+raw_material_received_january","liabilities_january":"bank_loan_initial-loan_repayment_december+raw_material_received_january"},"constraints":["production[p] <= raw_material_capacity[p] for each product p","cash_january >= min_cash_january","cash_january+receivables_january+inventory_january >= min_current_ratio_january*liabilities_january"],"objective":"maximize sum((price[p]-labor_cost[p]-material_cost[p])*production[p])"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = ("tape", "radio")

    labor_cost = {
        "tape": params["labor_cost_tape"],
        "radio": params["labor_cost_radio"],
    }
    material_cost = {
        "tape": params["material_cost_tape"],
        "radio": params["material_cost_radio"],
    }
    price = {
        "tape": params["price_tape"],
        "radio": params["price_radio"],
    }
    raw_material_capacity = {
        "tape": params["raw_material_capacity_tape"],
        "radio": params["raw_material_capacity_radio"],
    }

    cash_initial = params["cash_initial"]
    accounts_receivable_initial = params["accounts_receivable_initial"]
    inventory_initial = params["inventory_initial"]
    bank_loan_initial = params["bank_loan_initial"]
    ar_collection_december = params["ar_collection_december"]
    loan_repayment_december = params["loan_repayment_december"]
    rent_december = params["rent_december"]
    raw_material_received_january = params["raw_material_received_january"]
    min_cash_january = params["min_cash_january"]
    min_current_ratio_january = params["min_current_ratio_january"]

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=products, ordered=True)
    model.production = pyo.Var(model.products, domain=pyo.NonNegativeReals)

    model.labor = pyo.Expression(
        expr=sum(
            labor_cost[product] * model.production[product]
            for product in products
        )
    )
    model.materials_used = pyo.Expression(
        expr=sum(
            material_cost[product] * model.production[product]
            for product in products
        )
    )
    model.sales = pyo.Expression(
        expr=sum(
            price[product] * model.production[product]
            for product in products
        )
    )

    model.cash_january = pyo.Expression(
        expr=(
            cash_initial
            + ar_collection_december
            - loan_repayment_december
            - rent_december
            - model.labor
        )
    )
    model.receivables_january = pyo.Expression(
        expr=(
            accounts_receivable_initial
            - ar_collection_december
            + model.sales
        )
    )
    model.inventory_january = pyo.Expression(
        expr=(
            inventory_initial
            - model.materials_used
            + raw_material_received_january
        )
    )
    model.liabilities_january = pyo.Expression(
        expr=(
            bank_loan_initial
            - loan_repayment_december
            + raw_material_received_january
        )
    )

    def capacity_rule(instance, product):
        return (
            instance.production[product]
            <= raw_material_capacity[product]
        )

    model.material_capacity = pyo.Constraint(
        model.products, rule=capacity_rule
    )
    model.minimum_cash = pyo.Constraint(
        expr=model.cash_january >= min_cash_january
    )

    # The January shipment increases both inventory and accounts payable.
    # Cross multiplication expresses the required current ratio linearly.
    model.minimum_current_ratio = pyo.Constraint(
        expr=(
            model.cash_january
            + model.receivables_january
            + model.inventory_january
            >= min_current_ratio_january * model.liabilities_january
        )
    )

    model.profit_contribution = pyo.Objective(
        expr=sum(
            (
                price[product]
                - labor_cost[product]
                - material_cost[product]
            )
            * model.production[product]
            for product in products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except ApplicationError:
        return {"objective": None, "status": "solver_failed"}
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.profit_contribution))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}