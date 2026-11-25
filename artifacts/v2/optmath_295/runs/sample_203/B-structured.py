# IR: {"sets":{"consultants":[0,1,2,3],"projects":[0,1,2,3,4]},"params":{"consultant_hours":"params['consultant_hours'][i]","project_hours":"params['project_hours'][j]","capacity":"params['capacity'][i][j]","cost":"params['cost'][i][j]"},"variables":{"hours[i,j]":{"type":"continuous","lower_bound":0}},"constraints":["For each consultant i: sum_j hours[i,j] = consultant_hours[i]","For each project j: sum_i hours[i,j] = project_hours[j]","For each consultant-project pair (i,j): hours[i,j] <= capacity[i,j]"],"objective":"Minimize sum_i sum_j cost[i,j] * hours[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    consultant_hours = params["consultant_hours"]
    project_hours = params["project_hours"]
    capacity = params["capacity"]
    cost = params["cost"]

    model = pyo.ConcreteModel()
    model.consultants = pyo.RangeSet(0, 3)
    model.projects = pyo.RangeSet(0, 4)

    model.consultant_hours = pyo.Param(
        model.consultants,
        initialize=lambda mdl, i: consultant_hours[i],
    )
    model.project_hours = pyo.Param(
        model.projects,
        initialize=lambda mdl, j: project_hours[j],
    )
    model.capacity = pyo.Param(
        model.consultants,
        model.projects,
        initialize=lambda mdl, i, j: capacity[i][j],
    )
    model.cost = pyo.Param(
        model.consultants,
        model.projects,
        initialize=lambda mdl, i, j: cost[i][j],
    )

    model.hours = pyo.Var(
        model.consultants,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    def consultant_balance_rule(mdl, i):
        return (
            sum(mdl.hours[i, j] for j in mdl.projects)
            == mdl.consultant_hours[i]
        )

    model.consultant_balance = pyo.Constraint(
        model.consultants,
        rule=consultant_balance_rule,
    )

    def project_balance_rule(mdl, j):
        return (
            sum(mdl.hours[i, j] for i in mdl.consultants)
            == mdl.project_hours[j]
        )

    model.project_balance = pyo.Constraint(
        model.projects,
        rule=project_balance_rule,
    )

    def capacity_limit_rule(mdl, i, j):
        return mdl.hours[i, j] <= mdl.capacity[i, j]

    model.capacity_limit = pyo.Constraint(
        model.consultants,
        model.projects,
        rule=capacity_limit_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.hours[i, j]
            for i in model.consultants
            for j in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}