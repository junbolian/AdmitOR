import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_persons = 7
    n_projects = 7
    persons = range(n_persons)
    projects = range(n_projects)

    availability = params["availability"]
    demand = params["demand"]
    cost = params["cost"]
    pair_cap = params["pair_cap"]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(persons, projects, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in persons for j in projects),
        sense=pyo.minimize,
    )

    model.availability_con = pyo.Constraint(
        persons,
        rule=lambda m, i: sum(m.x[i, j] for j in projects) <= availability[i],
    )

    model.demand_con = pyo.Constraint(
        projects,
        rule=lambda m, j: sum(m.x[i, j] for i in persons) >= demand[j],
    )

    model.pair_cap_con = pyo.Constraint(
        persons,
        projects,
        rule=lambda m, i, j: m.x[i, j] <= pair_cap[i][j],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}