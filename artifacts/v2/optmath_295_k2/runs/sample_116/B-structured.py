# IR: {"sets":{"I":"0..7","J":"0..7"},"params":{"consultant_availability":"nonnegative[I]","project_demand":"nonnegative[J]","assignment_cost":"real[I,J]","assignment_capacity":"nonnegative[I,J]"},"variables":{"hours[I,J]":"continuous nonnegative"},"constraints":["sum(hours[i,j] for j in J) == consultant_availability[i] for i in I","sum(hours[i,j] for i in I) == project_demand[j] for j in J","hours[i,j] <= assignment_capacity[i,j] for i in I, j in J"],"objective":"minimize sum(assignment_cost[i,j] * hours[i,j] for i in I, j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.consultants = pyo.RangeSet(0, 7)
    model.projects = pyo.RangeSet(0, 7)

    model.consultant_availability = pyo.Param(
        model.consultants,
        initialize={
            i: params["consultant_availability"][i]
            for i in model.consultants
        },
        within=pyo.NonNegativeReals,
    )

    model.project_demand = pyo.Param(
        model.projects,
        initialize={
            j: params["project_demand"][j]
            for j in model.projects
        },
        within=pyo.NonNegativeReals,
    )

    model.assignment_cost = pyo.Param(
        model.consultants,
        model.projects,
        initialize={
            (i, j): params["assignment_cost"][i][j]
            for i in model.consultants
            for j in model.projects
        },
        within=pyo.Reals,
    )

    model.assignment_capacity = pyo.Param(
        model.consultants,
        model.projects,
        initialize={
            (i, j): params["assignment_capacity"][i][j]
            for i in model.consultants
            for j in model.projects
        },
        within=pyo.NonNegativeReals,
    )

    model.hours = pyo.Var(
        model.consultants,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mdl, i):
        return (
            sum(mdl.hours[i, j] for j in mdl.projects)
            == mdl.consultant_availability[i]
        )

    model.supply_constraints = pyo.Constraint(
        model.consultants,
        rule=supply_rule,
    )

    def demand_rule(mdl, j):
        return (
            sum(mdl.hours[i, j] for i in mdl.consultants)
            == mdl.project_demand[j]
        )

    model.demand_constraints = pyo.Constraint(
        model.projects,
        rule=demand_rule,
    )

    def capacity_rule(mdl, i, j):
        return mdl.hours[i, j] <= mdl.assignment_capacity[i, j]

    model.capacity_constraints = pyo.Constraint(
        model.consultants,
        model.projects,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[i, j] * model.hours[i, j]
            for i in model.consultants
            for j in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}