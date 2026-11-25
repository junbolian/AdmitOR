import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    employee_availability = params["employee_availability"]
    project_requirement = params["project_requirement"]
    assignment_cost = params["assignment_cost"]
    assignment_limit = params["assignment_limit"]

    n_emp = len(employee_availability)
    n_proj = len(project_requirement)
    emp_idx = range(n_emp)
    proj_idx = range(n_proj)
    pairs = [(i, j) for i in emp_idx for j in proj_idx]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(pairs, domain=pyo.NonNegativeReals)

    model.cost = pyo.Objective(
        expr=sum(assignment_cost[i][j] * model.x[i, j] for (i, j) in pairs),
        sense=pyo.minimize,
    )

    model.emp_cap = pyo.Constraint(
        emp_idx,
        rule=lambda m, i: sum(m.x[i, j] for j in proj_idx)
        <= employee_availability[i],
    )

    model.proj_demand = pyo.Constraint(
        proj_idx,
        rule=lambda m, j: sum(m.x[i, j] for i in emp_idx)
        >= project_requirement[j],
    )

    model.pair_limit = pyo.Constraint(
        pairs,
        rule=lambda m, i, j: m.x[i, j] <= assignment_limit[i][j],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}