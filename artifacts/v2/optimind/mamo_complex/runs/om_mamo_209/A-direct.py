import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    initial_inventory = params["initial_inventory"]
    regular_capacity = params["regular_capacity"]
    regular_cost = params["regular_cost"]
    overtime_cost = params["overtime_cost"]
    holding_cost = params["holding_cost"]

    quarters = list(range(4))

    model = pyo.ConcreteModel()

    model.Q = pyo.Set(initialize=quarters)

    model.regular = pyo.Var(model.Q, domain=pyo.NonNegativeReals)
    model.overtime = pyo.Var(model.Q, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.Q, domain=pyo.NonNegativeReals)

    model.regular_cap_con = pyo.Constraint(
        model.Q, rule=lambda mdl, t: mdl.regular[t] <= regular_capacity
    )

    def inventory_balance(mdl, t):
        if t == 0:
            return mdl.inventory[t] == initial_inventory + mdl.regular[t] + mdl.overtime[t] - demand[t]
        return mdl.inventory[t] == mdl.inventory[t - 1] + mdl.regular[t] + mdl.overtime[t] - demand[t]

    model.inv_balance_con = pyo.Constraint(model.Q, rule=inventory_balance)

    model.total_cost = pyo.Objective(
        expr=sum(
            regular_cost * model.regular[t]
            + overtime_cost * model.overtime[t]
            + holding_cost * model.inventory[t]
            for t in model.Q
        ),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}