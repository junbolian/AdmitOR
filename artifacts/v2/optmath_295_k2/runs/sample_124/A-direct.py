import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cap_limits = params["capacity_limits"]
    costs = params["costs"]

    n_people = len(supply)
    n_projects = len(demand)

    people = list(range(n_people))
    projects = list(range(n_projects))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=people)
    model.J = pyo.Set(initialize=projects)

    model.x = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals, bounds=lambda m, i, j: (0, cap_limits[i][j]))

    model.obj = pyo.Objective(
        expr=sum(costs[i][j] * model.x[i, j] for i in people for j in projects),
        sense=pyo.minimize,
    )

    model.supply_con = pyo.Constraint(
        model.P, rule=lambda m, i: sum(m.x[i, j] for j in projects) == supply[i]
    )

    model.demand_con = pyo.Constraint(
        model.J, rule=lambda m, j: sum(m.x[i, j] for i in people) == demand[j]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}