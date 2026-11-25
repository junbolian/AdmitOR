import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_ordering_cost = params["fixed_ordering_cost"]
    unit_purchase_cost = params["unit_purchase_cost"]
    holding_cost = params["holding_cost"]
    demand = params["demand"]
    order_limit = params["order_limit"]

    T = list(range(25))
    T_last = 24

    model = pyo.ConcreteModel()
    model.weeks = pyo.Set(initialize=T)

    # Binary order placement decision
    model.order_placed = pyo.Var(model.weeks, within=pyo.Binary)
    # Order quantity
    model.order_qty = pyo.Var(model.weeks, within=pyo.NonNegativeReals)
    # Inventory carried over to next week
    model.inventory = pyo.Var(model.weeks, within=pyo.NonNegativeReals)

    # Objective
    def obj_rule(m):
        return (
            sum(fixed_ordering_cost[t] * m.order_placed[t] for t in m.weeks)
            + sum(unit_purchase_cost[t] * m.order_qty[t] for t in m.weeks)
            + sum(holding_cost[t] * m.inventory[t] for t in m.weeks if t < T_last)
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Inventory balance: prev_inv + order = demand + inv
    # Start inventory zero
    def balance_first_rule(m):
        return m.order_qty[0] == demand[0] + m.inventory[0]
    model.balance_first = pyo.Constraint(rule=balance_first_rule)

    def balance_rule(m, t):
        if t == 0:
            return pyo.Constraint.Skip
        return m.inventory[t - 1] + m.order_qty[t] == demand[t] + m.inventory[t]
    model.balance = pyo.Constraint(model.weeks, rule=balance_rule)

    # Ending inventory zero
    def end_inv_rule(m):
        return m.inventory[T_last] == 0
    model.end_inv = pyo.Constraint(rule=end_inv_rule)

    # Order limit linked to binary
    def order_limit_rule(m, t):
        return m.order_qty[t] <= order_limit * m.order_placed[t]
    model.order_limit_con = pyo.Constraint(model.weeks, rule=order_limit_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}