import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = {0: params["profit_p0"], 1: params["profit_p1"]}
    holding_cost = params["holding_cost"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    grind_hrs = {0: params["grind_hours_per_unit_p0"], 1: params["grind_hours_per_unit_p1"]}
    drill_hrs = {0: params["drill_hours_per_unit_p0"], 1: params["drill_hours_per_unit_p1"]}
    bore_hrs = {0: params["bore_hours_per_unit_p0"], 1: params["bore_hours_per_unit_p1"]}
    inventory_limit = params["inventory_limit"]
    sales_limit = {0: params["sales_limit_p0"], 1: params["sales_limit_p1"]}
    target_inventory = params["target_inventory"]

    periods = list(range(4))
    products = [0, 1]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    model.produce = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)

    # Objective: maximize profit - holding cost
    model.obj = pyo.Objective(
        expr=sum(
            profit[j] * model.sales[j, t] - holding_cost * model.inventory[j, t]
            for j in model.P for t in model.T
        ),
        sense=pyo.maximize,
    )

    # Initial balance (period 0)
    model.init_balance = pyo.Constraint(
        model.P,
        rule=lambda m, j: m.produce[j, 0] == m.sales[j, 0] + m.inventory[j, 0],
    )

    # Inventory balance (periods 1..3)
    model.inv_balance = pyo.Constraint(
        model.P, [1, 2, 3],
        rule=lambda m, j, t: m.inventory[j, t - 1] + m.produce[j, t]
        == m.sales[j, t] + m.inventory[j, t],
    )

    # Inventory limits
    model.inv_limit = pyo.Constraint(
        model.P, model.T,
        rule=lambda m, j, t: m.inventory[j, t] <= inventory_limit,
    )

    # Sales limits
    model.sales_limit = pyo.Constraint(
        model.P, model.T,
        rule=lambda m, j, t: m.sales[j, t] <= sales_limit[j][t],
    )

    # Machine capacity constraints
    model.grinder_cap = pyo.Constraint(
        model.T,
        rule=lambda m, t: sum(grind_hrs[j] * m.produce[j, t] for j in m.P)
        <= grinder_capacity,
    )
    model.drill_cap = pyo.Constraint(
        model.T,
        rule=lambda m, t: sum(drill_hrs[j] * m.produce[j, t] for j in m.P)
        <= drill_capacity,
    )
    model.borer_cap = pyo.Constraint(
        model.T,
        rule=lambda m, t: sum(bore_hrs[j] * m.produce[j, t] for j in m.P)
        <= borer_capacity,
    )

    # Target ending inventory at period 3
    model.target_inv = pyo.Constraint(
        model.P,
        rule=lambda m, j: m.inventory[j, 3] == target_inventory,
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}