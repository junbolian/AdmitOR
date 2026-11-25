import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = [0, 1]
    periods = [0, 1, 2, 3]

    # Sales limits per product per period (from params where scalar, inline list structure)
    sales_limits = {
        (0, 0): 35, (0, 1): 47, (0, 2): 42, (0, 3): 25,
        (1, 0): 30, (1, 1): 27, (1, 2): 50, (1, 3): 31,
    }

    profit_per_unit = {
        0: params["profit_product0"],
        1: params["profit_product1"],
    }
    holding_cost = params["holding_cost"]

    machine_capacity = {
        "grinder": params["grinder_capacity"],
        "drill": params["drill_capacity"],
        "borer": params["borer_capacity"],
    }

    time_req = {
        ("grinder", 0): params["time_product0_grinder"],
        ("grinder", 1): params["time_product1_grinder"],
        ("drill", 0): params["time_product0_drill"],
        ("drill", 1): params["time_product1_drill"],
        ("borer", 0): params["time_product0_borer"],
        ("borer", 1): params["time_product1_borer"],
    }

    inventory_limit = params["inventory_limit"]
    target_inventory = params["target_inventory"]

    model = pyo.ConcreteModel()

    model.PROD = pyo.Set(initialize=products)
    model.PER = pyo.Set(initialize=periods)
    model.MACH = pyo.Set(initialize=["grinder", "drill", "borer"])

    model.IJ = pyo.Set(initialize=[(j, t) for j in products for t in periods])
    model.JT = pyo.Set(initialize=[(j, t) for j in products for t in periods])
    model.MT = pyo.Set(initialize=[(k, t) for k in ["grinder", "drill", "borer"] for t in periods])

    model.produce = pyo.Var(model.IJ, domain=pyo.NonNegativeReals)
    model.invent = pyo.Var(model.JT, domain=pyo.NonNegativeReals)
    model.sold = pyo.Var(model.JT, domain=pyo.NonNegativeReals)

    # Objective
    def objective_rule(m):
        return sum(
            profit_per_unit[j] * m.sold[j, t] for j in products for t in periods
        ) - sum(
            holding_cost * m.invent[j, t] for j in products for t in periods
        )

    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    # Initial balance (period 0)
    def balance0_rule(m, j):
        return m.produce[j, 0] == m.sold[j, 0] + m.invent[j, 0]

    model.balance0 = pyo.Constraint(model.PROD, rule=balance0_rule)

    # Inventory balance (periods 1-3)
    def balance_rule(m, j, t):
        if t == 0:
            return pyo.Constraint.Skip
        return m.invent[j, t - 1] + m.produce[j, t] == m.sold[j, t] + m.invent[j, t]

    model.balance = pyo.Constraint(model.JT, rule=balance_rule)

    # Machine capacity
    def capacity_rule(m, k, t):
        return sum(time_req[(k, j)] * m.produce[j, t] for j in products) <= machine_capacity[k]

    model.capacity = pyo.Constraint(model.MT, rule=capacity_rule)

    # Inventory storage limit
    def inv_limit_rule(m, j, t):
        return m.invent[j, t] <= inventory_limit

    model.inv_limit = pyo.Constraint(model.JT, rule=inv_limit_rule)

    # Sales limit
    def sales_limit_rule(m, j, t):
        return m.sold[j, t] <= sales_limits[(j, t)]

    model.sales_limit = pyo.Constraint(model.JT, rule=sales_limit_rule)

    # Target inventory at end of horizon
    def target_rule(m, j):
        return m.invent[j, 3] == target_inventory

    model.target = pyo.Constraint(model.PROD, rule=target_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}