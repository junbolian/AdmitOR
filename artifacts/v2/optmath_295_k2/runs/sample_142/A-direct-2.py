import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    capacity = params["capacity"]
    shipping_cost = [
        params["shipping_cost_f0"],
        params["shipping_cost_f1"],
        params["shipping_cost_f2"],
        params["shipping_cost_f3"],
    ]

    n_fac = 4
    n_cust = 10
    facs = list(range(n_fac))
    custs = list(range(n_cust))

    def sc(i, j):
        return shipping_cost[i][j]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(facs, custs, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(facs, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(fixed_cost[i] * model.y[i] for i in facs)
        + sum(sc(i, j) * model.x[i, j] for i in facs for j in custs),
        sense=pyo.minimize,
    )

    model.demand_con = pyo.Constraint(
        custs,
        rule=lambda m, j: sum(m.x[i, j] for i in facs) >= demand[j],
    )

    model.cap_con = pyo.Constraint(
        facs,
        rule=lambda m, i: sum(m.x[i, j] for j in custs) <= capacity[i] * m.y[i],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}