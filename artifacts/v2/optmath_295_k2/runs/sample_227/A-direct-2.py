import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    P = [1, 2, 3]
    S = [1, 2, 3, 4]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(P, S, domain=pyo.NonNegativeReals)

    model.profit = {
        (p, s): params[f"profit_p{p}_s{s}"] for p in P for s in S
    }
    model.demand = {
        (p, s): params[f"demand_p{p}_s{s}"] for p in P for s in S
    }

    model.obj = pyo.Objective(
        expr=sum(model.profit[p, s] * model.x[p, s] for p in P for s in S),
        sense=pyo.maximize,
    )

    model.demand_con = pyo.Constraint(
        P, S, rule=lambda model, p, s: model.x[p, s] == model.demand[p, s]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}