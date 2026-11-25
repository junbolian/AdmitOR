import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    T = 14
    fixed_ordering_costs = params["fixed_ordering_costs"]
    variable_ordering_costs = params["variable_ordering_costs"]
    inventory_holding_costs = params["inventory_holding_costs"]
    demand = params["demand"]
    order_capacity = params["order_capacity"]
    initial_inventory = params["initial_inventory"]
    final_inventory = params["final_inventory"]

    model = pyo.ConcreteModel()
    model.periods = pyo.RangeSet(1, T)

    model.setup = pyo.Var(model.periods, domain=pyo.Binary)
    model.qty = pyo.Var(model.periods, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.periods, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(
            fixed_ordering_costs[t - 1] * model.setup[t]
            + variable_ordering_costs[t - 1] * model.qty[t]
            + inventory_holding_costs[t - 1] * model.inv[t]
            for t in model.periods
        ),
        sense=pyo.minimize,
    )

    def balance_rule(m, t):
        prev = initial_inventory if t == 1 else m.inv[t - 1]
        return prev + m.qty[t] == m.inv[t] + demand[t - 1]

    model.balance = pyo.Constraint(model.periods, rule=balance_rule)

    def cap_rule(m, t):
        return m.qty[t] <= order_capacity[t - 1] * m.setup[t]

    model.capacity = pyo.Constraint(model.periods, rule=cap_rule)

    model.final_inv = pyo.Constraint(expr=model.inv[T] == final_inventory)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}