import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    clinics = [1, 2, 3, 4]

    stock = {i: params[f"stock"][i - 1] for i in clinics}
    demand = {i: params[f"demand"][i - 1] for i in clinics}

    cost = {
        (1, 2): params["cost_12"],
        (1, 3): params["cost_13"],
        (1, 4): params["cost_14"],
        (2, 1): params["cost_21"],
        (2, 3): params["cost_23"],
        (2, 4): params["cost_24"],
        (3, 1): params["cost_31"],
        (3, 2): params["cost_32"],
        (3, 4): params["cost_34"],
        (4, 1): params["cost_41"],
        (4, 2): params["cost_42"],
        (4, 3): params["cost_43"],
    }

    arcs = list(cost.keys())

    model = pyo.ConcreteModel()
    model.x = pyo.Var(arcs, domain=pyo.NonNegativeReals)
    model.obj = pyo.Objective(
        expr=sum(cost[(i, j)] * model.x[(i, j)] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    def balance_rule(m, c):
        inflow = sum(m.x[(i, c)] for (i, j) in arcs if j == c)
        outflow = sum(m.x[(c, j)] for (i, j) in arcs if i == c)
        return stock[c] + inflow - outflow >= demand[c]

    model.balance = pyo.Constraint(clinics, rule=balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}