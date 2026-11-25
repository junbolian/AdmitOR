# IR: {"sets":{"I":"0..7","J":"0..7"},"params":{"consultant_availability":"nonnegative real[I], from params","project_demand":"nonnegative real[J], from params","assignment_cost":"real[I,J], from params","assignment_capacity":"nonnegative real[I,J], from params"},"variables":{"hours":"nonnegative continuous[I,J]"},"constraints":["forall i: sum_j hours[i,j] == consultant_availability[i]","forall j: sum_i hours[i,j] == project_demand[j]","forall i,j: hours[i,j] <= assignment_capacity[i,j]"],"objective":"minimize sum_i sum_j assignment_cost[i,j] * hours[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    consultant_availability = params["consultant_availability"]
    project_demand = params["project_demand"]
    assignment_cost = params["assignment_cost"]
    assignment_capacity = params["assignment_capacity"]

    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 7)
    model.J = pyo.RangeSet(0, 7)

    model.consultant_availability = pyo.Param(
        model.I,
        initialize={i: consultant_availability[i] for i in model.I},
        within=pyo.NonNegativeReals,
    )
    model.project_demand = pyo.Param(
        model.J,
        initialize={j: project_demand[j] for j in model.J},
        within=pyo.NonNegativeReals,
    )
    model.assignment_cost = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): assignment_cost[i][j]
            for i in model.I
            for j in model.J
        },
        within=pyo.Reals,
    )
    model.assignment_capacity = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): assignment_capacity[i][j]
            for i in model.I
            for j in model.J
        },
        within=pyo.NonNegativeReals,
    )

    model.hours = pyo.Var(
        model.I, model.J, domain=pyo.NonNegativeReals
    )

    def supply_rule(instance, i):
        return (
            sum(instance.hours[i, j] for j in instance.J)
            == instance.consultant_availability[i]
        )

    def demand_rule(instance, j):
        return (
            sum(instance.hours[i, j] for i in instance.I)
            == instance.project_demand[j]
        )

    def capacity_rule(instance, i, j):
        return (
            instance.hours[i, j]
            <= instance.assignment_capacity[i, j]
        )

    model.supply_constraints = pyo.Constraint(
        model.I, rule=supply_rule
    )
    model.demand_constraints = pyo.Constraint(
        model.J, rule=demand_rule
    )
    model.capacity_constraints = pyo.Constraint(
        model.I, model.J, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[i, j] * model.hours[i, j]
            for i in model.I
            for j in model.J
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Unexpected solver exceptions must propagate.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}