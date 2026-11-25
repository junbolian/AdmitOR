import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["employee_availability"]
    requirements = params["project_requirements"]
    cost = params["assignment_cost"]
    limit = params["assignment_limit"]

    num_emp = len(availability)
    num_proj = len(requirements)

    model = pyo.ConcreteModel()

    model.emp = pyo.RangeSet(0, num_emp - 1)
    model.proj = pyo.RangeSet(0, num_proj - 1)

    def _bounds(mdl, i, j):
        return (0.0, limit[i][j])

    model.x = pyo.Var(model.emp, model.proj, bounds=_bounds)

    def _obj(mdl):
        return sum(cost[i][j] * mdl.x[i, j]
                   for i in mdl.emp for j in mdl.proj)

    model.total_cost = pyo.Objective(rule=_obj, sense=pyo.minimize)

    def _emp_avail(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.proj) == availability[i]

    model.emp_constraint = pyo.Constraint(model.emp, rule=_emp_avail)

    def _proj_req(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.emp) == requirements[j]

    model.proj_constraint = pyo.Constraint(model.proj, rule=_proj_req)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}