# IR: {"sets":{"P":["I","II"],"T":[7,8,9,10,11,12]},"params":{"demand_I":"12 monthly demands, Jan-Dec","demand_II":"12 monthly demands, Jan-Dec","prod_cost_I":"I unit cost, Jan-May","prod_cost_I_late":"I unit cost, Jun-Dec","prod_cost_II":"II unit cost, Jan-May","prod_cost_II_late":"II unit cost, Jun-Dec","cap_month":"combined monthly production capacity","vol_I":"I unit volume","vol_II":"II unit volume","wh_cap":"own warehouse volume capacity","hold_own":"own storage cost per volume-month","hold_rent":"total rented storage cost per volume-month"},"variables":{"production[p,t]":"nonnegative continuous units","own_inventory[p,t]":"nonnegative continuous end-of-month units","rented_inventory[p,t]":"nonnegative continuous end-of-month units"},"constraints":["For each p,t: previous total inventory + production[p,t] = demand[p,t] + own_inventory[p,t] + rented_inventory[p,t]; previous inventory is zero for July.","For each t: sum_p production[p,t] <= cap_month.","For each t: sum_p volume[p]*own_inventory[p,t] <= wh_cap."],"objective":"Minimize July-Dec production costs plus monthly volume-based costs of end-of-month own and rented inventory; use late production costs for all modeled months."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand_I = params["demand_I"]
    demand_II = params["demand_II"]
    prod_cost_I = params["prod_cost_I"]
    prod_cost_I_late = params["prod_cost_I_late"]
    prod_cost_II = params["prod_cost_II"]
    prod_cost_II_late = params["prod_cost_II_late"]
    cap_month = params["cap_month"]
    vol_I = params["vol_I"]
    vol_II = params["vol_II"]
    wh_cap = params["wh_cap"]
    hold_own = params["hold_own"]
    hold_rent = params["hold_rent"]

    if len(demand_I) != 12 or len(demand_II) != 12:
        raise ValueError("Demand sequences must contain 12 values, January through December.")

    products = ("I", "II")
    months = tuple(range(7, 13))
    demand_series = {"I": demand_I, "II": demand_II}
    early_costs = {"I": prod_cost_I, "II": prod_cost_II}
    late_costs = {"I": prod_cost_I_late, "II": prod_cost_II_late}

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=products, ordered=True)
    model.months = pyo.Set(initialize=months, ordered=True)

    model.demand = pyo.Param(
        model.products,
        model.months,
        initialize={
            (product, month): demand_series[product][month - 1]
            for product in products
            for month in months
        },
        within=pyo.NonNegativeReals,
    )
    model.unit_production_cost = pyo.Param(
        model.products,
        model.months,
        initialize={
            (product, month): (
                early_costs[product] if month <= 5 else late_costs[product]
            )
            for product in products
            for month in months
        },
    )
    model.unit_volume = pyo.Param(
        model.products,
        initialize={"I": vol_I, "II": vol_II},
        within=pyo.NonNegativeReals,
    )
    model.production_capacity = pyo.Param(
        initialize=cap_month, within=pyo.NonNegativeReals
    )
    model.warehouse_capacity = pyo.Param(
        initialize=wh_cap, within=pyo.NonNegativeReals
    )
    model.own_storage_rate = pyo.Param(initialize=hold_own)
    model.rented_storage_rate = pyo.Param(initialize=hold_rent)

    model.production = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )
    model.own_inventory = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )
    model.rented_inventory = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )

    def inventory_balance_rule(block, product, month):
        previous_inventory = (
            0
            if month == 7
            else (
                block.own_inventory[product, month - 1]
                + block.rented_inventory[product, month - 1]
            )
        )
        return (
            previous_inventory + block.production[product, month]
            == block.demand[product, month]
            + block.own_inventory[product, month]
            + block.rented_inventory[product, month]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.months, rule=inventory_balance_rule
    )

    def production_capacity_rule(block, month):
        return (
            sum(block.production[product, month] for product in block.products)
            <= block.production_capacity
        )

    model.monthly_production_limit = pyo.Constraint(
        model.months, rule=production_capacity_rule
    )

    def warehouse_capacity_rule(block, month):
        return (
            sum(
                block.unit_volume[product] * block.own_inventory[product, month]
                for product in block.products
            )
            <= block.warehouse_capacity
        )

    model.monthly_warehouse_limit = pyo.Constraint(
        model.months, rule=warehouse_capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_production_cost[product, month]
            * model.production[product, month]
            + model.unit_volume[product]
            * (
                model.own_storage_rate * model.own_inventory[product, month]
                + model.rented_storage_rate * model.rented_inventory[product, month]
            )
            for product in model.products
            for month in model.months
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}