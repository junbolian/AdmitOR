import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    individual_total_capacity = params["individual_total_capacity"]
    project_demand = params["project_demand"]
    assignment_cost = params["assignment_cost"]
    max_contribution_per_project = params["max_contribution_per_project"]

    num_individuals = len(individual_total_capacity)
    num_projects = len(project_demand)

    persons = range(num_individuals)
    projects = range(num_projects)

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=persons)
    model.J = pyo.Set(initialize=projects)

    model.x = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(
            assignment_cost[p][j] * mdl.x[p, j]
            for p in mdl.P
            for j in mdl.J
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.capacity_con = pyo.Constraint(
        model.P,
        rule=lambda mdl, p: sum(mdl.x[p, j] for j in mdl.J)
        == individual_total_capacity[p],
    )

    model.demand_con = pyo.Constraint(
        model.J,
        rule=lambda mdl, j: sum(mdl.x[p, j] for p in mdl.P)
        == project_demand[j],
    )

    model.limit_con = pyo.Constraint(
        model.P,
        model.J,
        rule=lambda mdl, p, j: mdl.x[p, j] <= max_contribution_per_project[p][j],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}