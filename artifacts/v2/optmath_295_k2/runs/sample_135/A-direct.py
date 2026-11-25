import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_p0 = params["profit_per_unit_p0"]
    profit_p1 = params["profit_per_unit_p1"]
    hold_cost = params["holding_cost_per_unit_per_period"]

    grinder_cap = params["grinder_capacity_period"]
    drill_cap = params["drill_capacity_period"]
    borer_cap = params["borer_capacity_period"]

    grinder_h_p0 = params["grinder_hours_per_unit_p0"]
    grinder_h_p1 = params["grinder_hours_per_unit_p1"]
    drill_h = params["drill_hours_per_unit"]
    borer_h = params["borer_hours_per_unit"]

    max_inv = params["max_inventory_per_product_per_period"]
    max_sales_p0 = params["max_sales_p0_period"]
    max_sales_p1 = params["max_sales_p1_period"]

    final_inv_p0 = params["final_inventory_p0"]
    final_inv_p1 = params["final_inventory_p1"]

    periods = [0, 1, 2, 3]
    products = [0, 1]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=periods)
    model.K = pyo.Set(initialize=products)

    model.produce = pyo.Var(model.K, model.P, domain=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.K, model.P, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.K, model.P, domain=pyo.NonNegativeReals)

    max_sales_map = {0: max_sales_p0, 1: max_sales_p1}
    grinder_hours_map = {0: grinder_h_p0, 1: grinder_h_p1}

    def obj_rule(mdl):
        revenue = sum(
            (profit_p0 if k == 0 else profit_p1) * mdl.sell[k, t]
            for k in mdl.K for t in mdl.P
        )
        holding = sum(hold_cost * mdl.inventory[k, t] for k in mdl.K for t in mdl.P)
        return revenue - holding

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Inventory balance: period 0
    def balance_p0_rule(mdl, k):
        return mdl.inventory[k, 0] == mdl.produce[k, 0] - mdl.sell[k, 0]

    model.balance_p0 = pyo.Constraint(model.K, rule=balance_p0_rule)

    # Inventory balance: subsequent periods
    def balance_sub_rule(mdl, k, t):
        return (
            mdl.inventory[k, t - 1] + mdl.produce[k, t]
            == mdl.sell[k, t] + mdl.inventory[k, t]
        )

    model.balance_sub = pyo.Constraint(
        model.K, [t for t in periods if t >= 1], rule=balance_sub_rule
    )

    # Machine capacity constraints
    model.grinder_cap = pyo.Constraint(
        model.P,
        rule=lambda mdl, t: sum(
            grinder_hours_map[k] * mdl.produce[k, t] for k in mdl.K
        ) <= grinder_cap[t],
    )

    model.drill_cap = pyo.Constraint(
        model.P,
        rule=lambda mdl, t: sum(drill_h * mdl.produce[k, t] for k in mdl.K)
        <= drill_cap[t],
    )

    model.borer_cap = pyo.Constraint(
        model.P,
        rule=lambda mdl, t: sum(borer_h * mdl.produce[k, t] for k in mdl.K)
        <= borer_cap[t],
    )

    # Inventory capacity
    model.inv_cap = pyo.Constraint(
        model.K, model.P, rule=lambda mdl, k, t: mdl.inventory[k, t] <= max_inv
    )

    # Maximum sales
    model.sales_cap = pyo.Constraint(
        model.K,
        model.P,
        rule=lambda mdl, k, t: mdl.sell[k, t] <= max_sales_map[k][t],
    )

    # Final inventory requirements
    model.final_inv_p0 = pyo.Constraint(expr=model.inventory[0, 3] == final_inv_p0)
    model.final_inv_p1 = pyo.Constraint(expr=model.inventory[1, 3] == final_inv_p1)

    solver = Highs()
    solver.solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}