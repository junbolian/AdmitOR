# IR: {"sets":{"C":[0,1,2,3],"P":[0,1,2,3,4]},"params":{"consultant_hours":"exact hours by consultant","project_hours":"exact hours by project","capacity":"maximum hours by consultant and project","cost":"cost per assigned hour by consultant and project"},"variables":{"hours[C,P]":"NonNegativeReals"},"constraints":["sum(hours[c,p] for p in P) == consultant_hours[c] for c in C","sum(hours[c,p] for c in C) == project_hours[p] for p in P","hours[c,p] <= capacity[c][p] for c in C, p in P"],"objective":"minimize sum(cost[c][p] * hours[c,p] for c in C, p in P)"}

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

    model.required_consultant_hours = pyo.Param(
        model.C,
        initialize={c: consultant_hours[c] for c in model.C},
    )
    model.required_project_hours = pyo.Param(
        model.P,
        initialize={p: project_hours[p] for p in model.P},
    )
    model.pair_capacity = pyo.Param(
        model.C,
        model.P,
        initialize={
            (c, p): capacity[c][p]
            for c in model.C
            for p in model.P
        },
    )
    model.unit_cost = pyo.Param(
        model.C,
        model.P,
        initialize={
            (c, p): cost[c][p]
            for c in model.C
            for p in model.P
        },
    )

    model.hours = pyo.Var(
        model.C,
        model.P,
        domain=pyo.NonNegativeReals,
    )

    def consultant_balance_rule(instance, c):
        return (
            sum(instance.hours[c, p] for p in instance.P)
            == instance.required_consultant_hours[c]
        )

    model.consultant_balance = pyo.Constraint(
        model.C,
        rule=consultant_balance_rule,
    )

    def project_balance_rule(instance, p):
        return (
            sum(instance.hours[c, p] for c in instance.C)
            == instance.required_project_hours[p]
        )

    model.project_balance = pyo.Constraint(
        model.P,
        rule=project_balance_rule,
    )

    def capacity_limit_rule(instance, c, p):
        return instance.hours[c, p] <= instance.pair_capacity[c, p]

    model.capacity_limit = pyo.Constraint(
        model.C,
        model.P,
        rule=capacity_limit_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[c, p] * model.hours[c, p]
            for c in model.C
            for p in model.P
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}