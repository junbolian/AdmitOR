import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    reg_cap = params["regular_capacity"]
    reg_cost = params["regular_cost"]
    ot_cap = params["overtime_capacity"]
    ot_cost = params["overtime_cost"]
    inv_cost = params["inventory_cost"]
    init_inv = params["initial_inventory"]

    months = list(range(6))
    model = pyo.ConcreteModel()

    model.M = pyo.Set(initialize=months, ordered=True)

    model.reg = pyo.Var(model.M, domain=pyo.NonNegativeReals)
    model.ot = pyo.Var(model.M, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.M, domain=pyo.NonNegativeReals)

    # Regular and overtime capacity limits
    model.reg_cap_con = pyo.Constraint(
        model.M, rule=lambda m, t: m.reg[t] <= reg_cap
    )
    model.ot_cap_con = pyo.Constraint(
        model.M, rule=lambda m, t: m.ot[t] <= ot_cap
    )

    # Inventory balance
    def inv_balance(m, t):
        prev = init_inv if t == 0 else m.inv[t - 1]
        return prev + m.reg[t] + m.ot[t] - m.inv[t] == demand[t]

    model.inv_balance_con = pyo.Constraint(model.M, rule=inv_balance)

    def total_cost(m):
        return sum(
            reg_cost * m.reg[t]
            + ot_cost * m.ot[t]
            + inv_cost * m.inv[t]
            for t in m.M
        )

    model.total_cost = pyo.Objective(rule=total_cost, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}