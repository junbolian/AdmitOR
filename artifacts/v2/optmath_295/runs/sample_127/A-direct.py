import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    T = 14

    fixed_cost = params["fixed_ordering_cost"]
    var_cost = params["variable_ordering_cost"]
    hold_cost = params["inventory_holding_cost"]
    demand = params["demand"]
    max_order = params["max_order_quantity"]
    init_inv = params["initial_inventory"]
    final_inv = params["final_inventory"]

    model = pyo.ConcreteModel()
    model.T = pyo.RangeSet(1, T)

    model.order_placed = pyo.Var(model.T, domain=pyo.Binary)
    model.order_qty = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.T, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            fixed_cost[t - 1] * m.order_placed[t]
            + var_cost[t - 1] * m.order_qty[t]
            + hold_cost[t - 1] * m.inventory[t]
            for t in m.T
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def balance_rule(m, t):
        prev = init_inv if t == 1 else m.inventory[t - 1]
        return prev + m.order_qty[t] == demand[t - 1] + m.inventory[t]

    model.balance = pyo.Constraint(model.T, rule=balance_rule)

    def link_rule(m, t):
        return m.order_qty[t] <= max_order * m.order_placed[t]

    model.link = pyo.Constraint(model.T, rule=link_rule)

    model.final_inv_con = pyo.Constraint(
        expr=model.inventory[T] == final_inv
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}