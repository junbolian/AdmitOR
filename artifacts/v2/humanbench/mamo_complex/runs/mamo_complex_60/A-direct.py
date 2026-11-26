import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    I = list(range(8))  # distribution centers
    J = list(range(8))  # retail stores

    opening = params["opening_cost"]
    transport = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(I, J, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(I, domain=pyo.Binary)

    model.total_cost = pyo.Objective(
        expr=sum(opening[i] * model.y[i] for i in I)
        + sum(transport[i][j] * model.x[i, j] for i in I for j in J),
        sense=pyo.minimize,
    )

    model.demand_con = pyo.Constraint(
        J, rule=lambda m, j: sum(m.x[i, j] for i in I) == demand[j]
    )
    model.capacity_con = pyo.Constraint(
        I, rule=lambda m, i: sum(m.x[i, j] for j in J) <= capacity[i] * m.y[i]
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}