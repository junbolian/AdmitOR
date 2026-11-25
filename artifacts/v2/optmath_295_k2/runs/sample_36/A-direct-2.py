import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    individual_total_capacity = params["individual_total_capacity"]
    project_demand = params["project_demand"]
    assignment_cost = params["assignment_cost"]
    max_contribution_per_project = params["max_contribution_per_project"]

    persons = list(range(len(individual_total_capacity)))
    projects = list(range(len(project_demand)))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=persons)
    model.J = pyo.Set(initialize=projects)

    model.x = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(assignment_cost[p][j] * mdl.x[p, j]
                   for p in persons for j in projects)
    model.cost_obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.capacity_cons = pyo.Constraint(
        model.P,
        rule=lambda mdl, p: sum(mdl.x[p, j] for j in projects)
        == individual_total_capacity[p],
    )

    model.demand_cons = pyo.Constraint(
        model.J,
        rule=lambda mdl, j: sum(mdl.x[p, j] for p in persons)
        == project_demand[j],
    )

    model.limit_cons = pyo.Constraint(
        model.P, model.J,
        rule=lambda mdl, p, j: mdl.x[p, j]
        <= max_contribution_per_project[p][j],
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.cost_obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or unsolvable"}