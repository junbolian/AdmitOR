import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    products = [0, 1]
    periods = [0, 1, 2, 3]
    machines = ["grinders", "drills", "borers"]

    profit = params["profit_per_unit"]
    hold = params["holding_cost"]
    mh = params["machine_hours_per_unit"]
    caps = {
        "grinders": params["grinder_capacity"],
        "drills": params["drill_capacity"],
        "borers": params["borer_capacity"],
    }
    inv_lim = params["inventory_limit"]
    sales_lim = {
        0: params["sales_limit_product0"],
        1: params["sales_limit_product1"],
    }
    target_inv = params["target_inventory"]

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)
    model.M = pyo.Set(initialize=machines)

    model.prod = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        rule=lambda m: sum(profit[k] * m.sales[k, t] for k in m.P for t in m.T)
        - sum(hold * m.inv[k, t] for k in m.P for t in m.T),
        sense=pyo.maximize,
    )

    # Balance constraints
    model.bal0 = pyo.Constraint(
        model.P,
        rule=lambda m, k: m.prod[k, 0] == m.sales[k, 0] + m.inv[k, 0],
    )
    model.bal = pyo.Constraint(
        model.P,
        [t for t in periods if t >= 1],
        rule=lambda m, k, t: m.inv[k, t - 1] + m.prod[k, t]
        == m.sales[k, t] + m.inv[k, t],
    )

    # Machine capacity constraints
    model.mach = pyo.Constraint(
        model.M,
        model.T,
        rule=lambda m, i, t: sum(
            mh[i] * m.prod[k, t] for k in m.P
        )
        <= caps[i][t],
    )

    # Inventory limits
    model.invlim = pyo.Constraint(
        model.P, model.T, rule=lambda m, k, t: m.inv[k, t] <= inv_lim
    )

    # Sales limits
    model.sl = pyo.Constraint(
        model.P, model.T, rule=lambda m, k, t: m.sales[k, t] <= sales_lim[k][t]
    )

    # Target inventory at end of horizon
    model.tgt = pyo.Constraint(
        model.P, rule=lambda m, k: m.inv[k, 3] == target_inv
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}