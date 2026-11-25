import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_fac = 4
    n_cust = 10
    facs = list(range(n_fac))
    custs = list(range(n_cust))

    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    capacity = params["capacity"]
    ship_cost = [
        params["shipping_cost_f0"],
        params["shipping_cost_f1"],
        params["shipping_cost_f2"],
        params["shipping_cost_f3"],
    ]

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=facs)
    model.C = pyo.Set(initialize=custs)
    model.FC = pyo.Set(initialize=[(i, j) for i in facs for j in custs])

    model.x = pyo.Var(model.FC, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.F, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(fixed_cost[i] * model.y[i] for i in facs)
        + sum(ship_cost[i][j] * model.x[i, j] for i, j in model.FC),
        sense=pyo.minimize,
    )

    model.demand_con = pyo.Constraint(
        model.C,
        rule=lambda m, j: sum(m.x[i, j] for i in m.F) == demand[j],
    )

    model.cap_con = pyo.Constraint(
        model.F,
        rule=lambda m, i: sum(m.x[i, j] for j in m.C) <= capacity[i] * m.y[i],
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}