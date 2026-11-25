import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    num_centers = len(opening_cost)
    num_hospitals = len(demand)
    centers = range(num_centers)
    hospitals = range(num_hospitals)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(centers, within=pyo.Binary)
    model.y = pyo.Var(hospitals, centers, within=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(opening_cost[j] * model.x[j] for j in centers)
        + sum(transport_cost[i][j] * model.y[i, j] for i in hospitals for j in centers),
        sense=pyo.minimize,
    )

    model.assign = pyo.Constraint(
        hospitals,
        rule=lambda m, i: sum(m.y[i, j] for j in centers) == 1,
    )

    model.cap = pyo.Constraint(
        centers,
        rule=lambda m, j: sum(demand[i] * m.y[i, j] for i in hospitals) <= capacity[j] * m.x[j],
    )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}