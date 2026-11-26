import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_dc = 8
    n_store = 5

    model = pyo.ConcreteModel()

    model.dc = pyo.RangeSet(0, n_dc - 1)
    model.store = pyo.RangeSet(0, n_store - 1)

    model.open_var = pyo.Var(model.dc, domain=pyo.Binary)
    model.flow = pyo.Var(model.dc, model.store, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(opening_cost[i] * model.open_var[i] for i in model.dc)
        + sum(transport_cost[i][j] * model.flow[i, j] for i in model.dc for j in model.store),
        sense=pyo.minimize,
    )

    model.demand_con = pyo.Constraint(
        model.store,
        rule=lambda m, j: sum(m.flow[i, j] for i in m.dc) >= demand[j],
    )

    model.capacity_con = pyo.Constraint(
        model.dc,
        rule=lambda m, i: sum(m.flow[i, j] for j in m.store) <= capacity[i] * m.open_var[i],
    )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}