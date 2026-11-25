import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    employee_availability = params["employee_availability"]
    project_requirements = params["project_requirements"]
    assignment_costs = params["assignment_costs"]
    pair_capacities = params["pair_capacities"]

    n_emp = len(employee_availability)
    n_proj = len(project_requirements)

    model = pyo.ConcreteModel()

    model.emp = pyo.RangeSet(0, n_emp - 1)
    model.proj = pyo.RangeSet(0, n_proj - 1)

    model.x = pyo.Var(model.emp, model.proj, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            assignment_costs[i][j] * m.x[i, j]
            for i in range(n_emp)
            for j in range(n_proj)
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def emp_avail_rule(m, i):
        return sum(m.x[i, j] for j in range(n_proj)) <= employee_availability[i]

    model.emp_avail_con = pyo.Constraint(model.emp, rule=emp_avail_rule)

    def proj_req_rule(m, j):
        return sum(m.x[i, j] for i in range(n_emp)) == project_requirements[j]

    model.proj_req_con = pyo.Constraint(model.proj, rule=proj_req_rule)

    def pair_cap_rule(m, i, j):
        return m.x[i, j] <= pair_capacities[i][j]

    model.pair_cap_con = pyo.Constraint(model.emp, model.proj, rule=pair_cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}