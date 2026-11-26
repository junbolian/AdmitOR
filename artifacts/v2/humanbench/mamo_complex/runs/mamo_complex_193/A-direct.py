import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    num_dc = len(opening_cost)
    num_store = len(demand)
    dcs = list(range(num_dc))
    stores = list(range(num_store))

    model = pyo.ConcreteModel()

    model.DC = pyo.Set(initialize=dcs)

    model.open = pyo.Var(model.DC, domain=pyo.Binary)
    model.flow = pyo.Var(model.DC, stores, domain=pyo.NonNegativeReals)

    model.total_cost = pyo.Objective(
        expr=sum(opening_cost[i] * model.open[i] for i in dcs)
        + sum(transport_cost[i][j] * model.flow[i, j] for i in dcs for j in stores),
        sense=pyo.minimize,
    )

    model.demand_sat = pyo.Constraint(
        stores,
        rule=lambda m, j: sum(m.flow[i, j] for i in dcs) == demand[j],
    )

    model.capacity_limit = pyo.Constraint(
        model.DC,
        rule=lambda m, i: sum(m.flow[i, j] for j in stores)
        <= capacity[i] * m.open[i],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}