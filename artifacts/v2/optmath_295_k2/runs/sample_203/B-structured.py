# IR: {"sets":{"C":[0,1,2,3],"P":[0,1,2,3,4]},"params":{"consultant_hours":"C-indexed exact hours","project_hours":"P-indexed exact hours","capacity":"C-by-P maximum hours","cost":"C-by-P cost coefficients"},"variables":{"hours[c,p]":"NonNegativeReals"},"constraints":["sum_p hours[c,p] == consultant_hours[c] for c in C","sum_c hours[c,p] == project_hours[p] for p in P","hours[c,p] <= capacity[c,p] for (c,p) in C x P"],"objective":"minimize sum_(c,p) cost[c,p] * hours[c,p]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    consultant_hours = params["consultant_hours"]
    project_hours = params["project_hours"]
    capacity = params["capacity"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.C = pyo.RangeSet(0, 3)
    model.P = pyo.RangeSet(0, 4)

    model.consultant_hours = pyo.Param(
        model.C,
        initialize=lambda mdl, c: consultant_hours[c],
    )
    model.project_hours = pyo.Param(
        model.P,
        initialize=lambda mdl, p: project_hours[p],
    )
    model.capacity = pyo.Param(
        model.C,
        model.P,
        initialize=lambda mdl, c, p: capacity[c][p],
    )
    model.cost = pyo.Param(
        model.C,
        model.P,
        initialize=lambda mdl, c, p: cost[c][p],
    )

    model.hours = pyo.Var(
        model.C,
        model.P,
        domain=pyo.NonNegativeReals,
    )

    def consultant_balance_rule(mdl, c):
        return (
            sum(mdl.hours[c, p] for p in mdl.P)
            == mdl.consultant_hours[c]
        )

    model.consultant_balance = pyo.Constraint(
        model.C,
        rule=consultant_balance_rule,
    )

    def project_balance_rule(mdl, p):
        return (
            sum(mdl.hours[c, p] for c in mdl.C)
            == mdl.project_hours[p]
        )

    model.project_balance = pyo.Constraint(
        model.P,
        rule=project_balance_rule,
    )

    def capacity_limit_rule(mdl, c, p):
        return mdl.hours[c, p] <= mdl.capacity[c, p]

    model.capacity_limit = pyo.Constraint(
        model.C,
        model.P,
        rule=capacity_limit_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[c, p] * model.hours[c, p]
            for c in model.C
            for p in model.P
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}