import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    num_centers = len(opening_cost)
    num_stores = len(demand)

    centers = list(range(num_centers))
    stores = list(range(num_stores))

    model = pyo.ConcreteModel()

    model.centers = pyo.Set(initialize=centers)
    model.stores = pyo.Set(initialize=stores)
    model.links = pyo.Set(
        initialize=[(c, s) for c in centers for s in stores], dimen=2
    )

    model.y = pyo.Var(model.centers, domain=pyo.Binary)
    model.x = pyo.Var(model.links, domain=pyo.NonNegativeReals)

    model.opening_cost_expr = pyo.Expression(
        expr=sum(opening_cost[c] * model.y[c] for c in model.centers)
    )
    model.transport_cost_expr = pyo.Expression(
        expr=sum(
            transport_cost[c][s] * model.x[c, s] for c, s in model.links
        )
    )
    model.total_cost = pyo.Objective(
        expr=model.opening_cost_expr + model.transport_cost_expr,
        sense=pyo.minimize,
    )

    model.demand_con = pyo.Constraint(
        model.stores,
        rule=lambda m, s: sum(m.x[c, s] for c in m.centers) == demand[s],
    )

    model.capacity_con = pyo.Constraint(
        model.centers,
        rule=lambda m, c: sum(m.x[c, s] for s in m.stores) <= capacity[c] * m.y[c],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}