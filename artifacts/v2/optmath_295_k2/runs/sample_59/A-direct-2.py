import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    T = 6

    setup_cost = params["fixed_setup_cost"]
    var_cost = params["variable_production_cost"]
    hold_cost = params["inventory_holding_cost"]
    back_cost = params["backlogging_cost"]
    demand = params["demand"]
    cap = params["production_capacity"]

    model = pyo.ConcreteModel()
    model.T = pyo.RangeSet(1, T)

    model.produce = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.setup = pyo.Var(model.T, domain=pyo.Binary)
    model.inv = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.back = pyo.Var(model.T, domain=pyo.NonNegativeReals)

    def balance_rule(m, t):
        inv_prev = m.inv[t - 1] if t > 1 else 0.0
        back_prev = m.back[t - 1] if t > 1 else 0.0
        return inv_prev + m.produce[t] + m.back[t] == demand[t - 1] + m.inv[t] + back_prev

    model.balance = pyo.Constraint(model.T, rule=balance_rule)

    model.end_inv = pyo.Constraint(expr=model.inv[T] == 0.0)
    model.end_back = pyo.Constraint(expr=model.back[T] == 0.0)

    def cap_rule(m, t):
        return m.produce[t] <= cap * m.setup[t]

    model.cap = pyo.Constraint(model.T, rule=cap_rule)

    def obj_rule(m):
        return sum(
            setup_cost[t - 1] * m.setup[t]
            + var_cost[t - 1] * m.produce[t]
            + hold_cost[t - 1] * m.inv[t]
            + back_cost[t - 1] * m.back[t]
            for t in m.T
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}