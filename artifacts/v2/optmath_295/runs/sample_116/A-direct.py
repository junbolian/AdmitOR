import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    consultant_availability = params["consultant_availability"]
    project_requirements = params["project_requirements"]
    assignment_costs = params["assignment_costs"]
    assignment_capacity = params["assignment_capacity"]

    n_consultants = len(consultant_availability)
    n_projects = len(project_requirements)

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, n_consultants - 1)
    model.J = pyo.RangeSet(0, n_projects - 1)

    model.x = pyo.Var(model.I, model.J, within=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(
            assignment_costs[i][j] * mdl.x[i, j]
            for i in range(n_consultants)
            for j in range(n_projects)
        )

    model.cost_obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in range(n_projects)) == consultant_availability[i]

    model.supply_con = pyo.Constraint(model.I, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in range(n_consultants)) == project_requirements[j]

    model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

    def cap_rule(mdl, i, j):
        return mdl.x[i, j] <= assignment_capacity[i][j]

    model.cap_con = pyo.Constraint(model.I, model.J, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost_obj))
    return {"objective": obj_val, "status": "optimal"}