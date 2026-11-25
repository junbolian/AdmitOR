import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    grinder_hours_per_unit = params["grinder_hours_per_unit"]
    drill_hours_per_unit = params["drill_hours_per_unit"]
    borer_hours_per_unit = params["borer_hours_per_unit"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    inventory_limit = params["inventory_limit"]
    sales_limit = params["sales_limit"]
    target_inventory = params["target_inventory"]

    products = [0, 1]
    periods = [0, 1, 2, 3]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    model.prod = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            profit_per_unit[p] * m.sell[p, t] - holding_cost * m.inv[p, t]
            for p in m.P for t in m.T
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Initial balance (t = 0)
    def balance_first_rule(m, p):
        t0 = periods[0]
        return m.prod[p, t0] == m.sell[p, t0] + m.inv[p, t0]

    model.balance_first = pyo.Constraint(model.P, rule=balance_first_rule)

    # Inventory balance (t >= 1)
    def balance_rule(m, p, t):
        if t == periods[0]:
            return pyo.Constraint.Skip
        return m.inv[p, t - 1] + m.prod[p, t] == m.sell[p, t] + m.inv[p, t]

    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    # Grinder capacity
    def grinder_rule(m, t):
        return sum(grinder_hours_per_unit[p] * m.prod[p, t] for p in m.P) <= grinder_capacity

    model.grinder = pyo.Constraint(model.T, rule=grinder_rule)

    # Drill capacity
    def drill_rule(m, t):
        return sum(drill_hours_per_unit[p] * m.prod[p, t] for p in m.P) <= drill_capacity

    model.drill = pyo.Constraint(model.T, rule=drill_rule)

    # Borer capacity
    def borer_rule(m, t):
        return sum(borer_hours_per_unit[p] * m.prod[p, t] for p in m.P) <= borer_capacity

    model.borer = pyo.Constraint(model.T, rule=borer_rule)

    # Inventory limits
    def inv_limit_rule(m, p, t):
        return m.inv[p, t] <= inventory_limit

    model.inv_limit = pyo.Constraint(model.P, model.T, rule=inv_limit_rule)

    # Sales limits
    def sales_limit_rule(m, p, t):
        return m.sell[p, t] <= sales_limit[p][t]

    model.sales_limit = pyo.Constraint(model.P, model.T, rule=sales_limit_rule)

    # Target inventory at end of horizon
    def target_rule(m, p):
        return m.inv[p, periods[-1]] == target_inventory[p]

    model.target = pyo.Constraint(model.P, rule=target_rule)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}