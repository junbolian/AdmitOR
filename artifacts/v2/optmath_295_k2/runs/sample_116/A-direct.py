import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["consultant_availability"]
    demand = params["project_demand"]
    cost = params["assignment_cost"]
    capacity = params["assignment_capacity"]

    n_consultants = len(availability)
    n_projects = len(demand)

    model = pyo.ConcreteModel()

    model.consultants = pyo.RangeSet(0, n_consultants - 1)
    model.projects = pyo.RangeSet(0, n_projects - 1)

    model.hours = pyo.Var(
        model.consultants, model.projects, domain=pyo.NonNegativeReals
    )

    def obj_rule(mdl):
        return sum(
            cost[i][j] * mdl.hours[i, j]
            for i in mdl.consultants
            for j in mdl.projects
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(mdl, i):
        return sum(mdl.hours[i, j] for j in mdl.projects) == availability[i]

    model.supply = pyo.Constraint(model.consultants, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.hours[i, j] for i in mdl.consultants) == demand[j]

    model.demand = pyo.Constraint(model.projects, rule=demand_rule)

    def cap_rule(mdl, i, j):
        return mdl.hours[i, j] <= capacity[i][j]

    model.capacity = pyo.Constraint(
        model.consultants, model.projects, rule=cap_rule
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": str(exc)[:100] or "infeasible"}