import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["employee_availability"]
    requirement = params["project_requirement"]
    cost = params["assignment_cost"]
    limit = params["assignment_limit"]

    n_emp = len(availability)
    n_proj = len(requirement)

    model = pyo.ConcreteModel()

    model.E = pyo.RangeSet(0, n_emp - 1)
    model.P = pyo.RangeSet(0, n_proj - 1)

    model.x = pyo.Var(model.E, model.P, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in model.E for j in model.P),
        sense=pyo.minimize,
    )

    model.emp_cap = pyo.Constraint(
        model.E,
        rule=lambda m, i: sum(m.x[i, j] for j in m.P) <= availability[i],
    )

    model.proj_req = pyo.Constraint(
        model.P,
        rule=lambda m, j: sum(m.x[i, j] for i in m.E) >= requirement[j],
    )

    model.pair_lim = pyo.Constraint(
        model.E,
        model.P,
        rule=lambda m, i, j: m.x[i, j] <= limit[i][j],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}