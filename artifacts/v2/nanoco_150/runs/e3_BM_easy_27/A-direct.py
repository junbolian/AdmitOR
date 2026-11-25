import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    route_revenue = params["route_revenue"]
    airport_capacity = params["airport_capacity"]

    edges = [
        (0, 7), (0, 8), (0, 9), (1, 5), (1, 9), (2, 3), (2, 9),
        (3, 4), (3, 6), (3, 9), (4, 5), (5, 6), (5, 9), (6, 9),
        (7, 8), (7, 9), (8, 9),
    ]
    airports = list(range(10))

    model = pyo.ConcreteModel()
    model.routes = pyo.Set(initialize=list(range(len(edges))))
    model.ports = pyo.Set(initialize=airports)

    model.select = pyo.Var(model.routes, domain=pyo.Binary)

    model.revenue = pyo.Objective(
        expr=sum(route_revenue[k] * model.select[k] for k in model.routes),
        sense=pyo.maximize,
    )

    def cap_rule(mdl, p):
        return sum(
            mdl.select[k]
            for k in mdl.routes
            if p == edges[k][0] or p == edges[k][1]
        ) <= airport_capacity[p]

    model.capacity = pyo.Constraint(model.ports, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.revenue))
    return {"objective": obj_val, "status": "optimal"}