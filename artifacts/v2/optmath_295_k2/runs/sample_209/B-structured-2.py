# IR: {"sets":{"I":"0..6","J":"0..6"},"params":{"person_availability":"nonnegative real[I]","project_requirement":"nonnegative real[J]","assignment_cost":"real[I,J]","assignment_upper_limit":"nonnegative real[I,J]"},"variables":{"hours[i,j]":"continuous nonnegative real, i in I, j in J"},"constraints":["sum(j in J, hours[i,j]) <= person_availability[i] for i in I","sum(i in I, hours[i,j]) == project_requirement[j] for j in J","hours[i,j] <= assignment_upper_limit[i,j] for i in I, j in J"],"objective":"minimize sum(i in I, j in J, assignment_cost[i,j]*hours[i,j])"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    person_availability = params["person_availability"]
    project_requirement = params["project_requirement"]
    assignment_cost = params["assignment_cost"]
    assignment_upper_limit = params["assignment_upper_limit"]

    model = pyo.ConcreteModel()
    model.persons = pyo.Set(initialize=range(7), ordered=True)
    model.projects = pyo.Set(initialize=range(7), ordered=True)

    model.person_availability = pyo.Param(
        model.persons,
        initialize={i: person_availability[i] for i in model.persons},
        within=pyo.NonNegativeReals,
    )
    model.project_requirement = pyo.Param(
        model.projects,
        initialize={j: project_requirement[j] for j in model.projects},
        within=pyo.NonNegativeReals,
    )
    model.assignment_cost = pyo.Param(
        model.persons,
        model.projects,
        initialize={
            (i, j): assignment_cost[i][j]
            for i in model.persons
            for j in model.projects
        },
        within=pyo.Reals,
    )
    model.assignment_upper_limit = pyo.Param(
        model.persons,
        model.projects,
        initialize={
            (i, j): assignment_upper_limit[i][j]
            for i in model.persons
            for j in model.projects
        },
        within=pyo.NonNegativeReals,
    )

    model.hours = pyo.Var(
        model.persons,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    def availability_rule(mdl, i):
        return (
            sum(mdl.hours[i, j] for j in mdl.projects)
            <= mdl.person_availability[i]
        )

    model.availability_constraints = pyo.Constraint(
        model.persons, rule=availability_rule
    )

    def requirement_rule(mdl, j):
        return (
            sum(mdl.hours[i, j] for i in mdl.persons)
            == mdl.project_requirement[j]
        )

    model.requirement_constraints = pyo.Constraint(
        model.projects, rule=requirement_rule
    )

    def assignment_limit_rule(mdl, i, j):
        return mdl.hours[i, j] <= mdl.assignment_upper_limit[i, j]

    model.assignment_limit_constraints = pyo.Constraint(
        model.persons, model.projects, rule=assignment_limit_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[i, j] * model.hours[i, j]
            for i in model.persons
            for j in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}