import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    T = 4
    P = 2
    sales_limits_p0 = [20, 46, 30, 26]
    sales_limits_p1 = [45, 36, 50, 42]
    sales_limit = {0: sales_limits_p0, 1: sales_limits_p1}

    model = pyo.ConcreteModel()
    model.T = pyo.RangeSet(0, T - 1)
    model.P = pyo.RangeSet(0, P - 1)

    model.x = pyo.Var(model.T, model.P, domain=pyo.NonNegativeReals)
    model.s = pyo.Var(model.T, model.P, domain=pyo.NonNegativeReals)
    model.h = pyo.Var(model.T, model.P, domain=pyo.NonNegativeReals)

    profit = [params["profit_per_unit_product0"], params["profit_per_unit_product1"]]
    hold_cost = params["holding_cost_per_unit_per_period"]

    grinder_hours = [params["grinder_hours_product0"], params["grinder_hours_product1"]]
    drill_hours = [params["drill_hours_product0"], params["drill_hours_product1"]]
    borer_hours = [params["borer_hours_product0"], params["borer_hours_product1"]]

    grinder_cap = params["grinder_capacity_per_period"]
    drill_cap = params["drill_capacity_per_period"]
    borer_cap = params["borer_capacity_per_period"]

    max_inv = [params["max_inventory_product0"], params["max_inventory_product1"]]
    target_inv = [params["target_inventory_product0"], params["target_inventory_product1"]]

    def obj_rule(m):
        return sum(profit[p] * m.s[t, p] for t in m.T for p in m.P) \
            - hold_cost * sum(m.h[t, p] for t in m.T for p in m.P)

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def init_balance_rule(m, p):
        return m.x[0, p] == m.s[0, p] + m.h[0, p]

    model.init_balance = pyo.Constraint(model.P, rule=init_balance_rule)

    def inv_balance_rule(m, t, p):
        return m.h[t - 1, p] + m.x[t, p] == m.s[t, p] + m.h[t, p]

    model.inv_balance = pyo.Constraint(
        pyo.RangeSet(1, T - 1), model.P, rule=inv_balance_rule
    )

    def grinder_rule(m, t):
        return sum(grinder_hours[p] * m.x[t, p] for p in m.P) <= grinder_cap

    model.grinder_cap = pyo.Constraint(model.T, rule=grinder_rule)

    def drill_rule(m, t):
        return sum(drill_hours[p] * m.x[t, p] for p in m.P) <= drill_cap

    model.drill_cap = pyo.Constraint(model.T, rule=drill_rule)

    def borer_rule(m, t):
        return sum(borer_hours[p] * m.x[t, p] for p in m.P) <= borer_cap

    model.borer_cap = pyo.Constraint(model.T, rule=borer_rule)

    def inv_max_rule(m, t, p):
        return m.h[t, p] <= max_inv[p]

    model.inv_max = pyo.Constraint(model.T, model.P, rule=inv_max_rule)

    def sales_rule(m, t, p):
        return m.s[t, p] <= sales_limit[p][t]

    model.sales_max = pyo.Constraint(model.T, model.P, rule=sales_rule)

    def terminal_rule(m, p):
        return m.h[T - 1, p] == target_inv[p]

    model.terminal_inv = pyo.Constraint(model.P, rule=terminal_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}