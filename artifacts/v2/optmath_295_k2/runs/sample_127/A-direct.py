import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    T = 14
    periods = range(1, T + 1)

    fixed_cost = params["fixed_ordering_costs"]
    var_cost = params["variable_ordering_costs"]
    hold_cost = params["inventory_holding_costs"]
    demand = params["demand"]
    order_cap = params["order_capacity"]
    init_inv = params["initial_inventory"]
    final_inv = params["final_inventory"]

    model = pyo.ConcreteModel()

    model.T = pyo.Set(initialize=periods)

    model.order = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.setup = pyo.Var(model.T, domain=pyo.Binary)

    model.cost = pyo.Objective(
        expr=sum(
            fixed_cost[t - 1] * model.setup[t]
            + var_cost[t - 1] * model.order[t]
            + hold_cost[t - 1] * model.inv[t]
            for t in model.T
        ),
        sense=pyo.minimize,
    )

    model.balance = pyo.Constraint(
        model.T,
        rule=lambda model, t: (
            (init_inv if t == 1 else model.inv[t - 1]) + model.order[t]
            == demand[t - 1] + model.inv[t]
        ),
    )

    model.capacity = pyo.Constraint(
        model.T,
        rule=lambda model, t: model.order[t] <= order_cap * model.setup[t],
    )

    model.final_balance = pyo.Constraint(
        expr=model.inv[T] == final_inv
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}