# IR: {"sets":{"participants":[0,1,2,3,4],"cars":[0,1,2,3]},"params":{"participant_interest":"binary matrix indexed by participant and car","max_assignments_per_participant":"nonnegative participant capacity","max_assignments_per_car":"nonnegative car capacity"},"variables":{"assignment[p,c]":"Binary"},"constraints":["assignment[p,c] <= participant_interest[p][c] for each participant p and car c","sum_c assignment[p,c] <= max_assignments_per_participant for each participant p","sum_p assignment[p,c] <= max_assignments_per_car for each car c"],"objective":"maximize sum_p sum_c assignment[p,c]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    participant_interest = params["participant_interest"]
    participant_capacity = params["max_assignments_per_participant"]
    car_capacity = params["max_assignments_per_car"]

    model = pyo.ConcreteModel()
    model.participants = pyo.RangeSet(0, 4)
    model.cars = pyo.RangeSet(0, 3)

    model.interest = pyo.Param(
        model.participants,
        model.cars,
        initialize={
            (participant, car): participant_interest[participant][car]
            for participant in model.participants
            for car in model.cars
        },
        within=pyo.Binary,
    )
    model.participant_capacity = pyo.Param(
        initialize=participant_capacity,
        within=pyo.NonNegativeReals,
    )
    model.car_capacity = pyo.Param(
        initialize=car_capacity,
        within=pyo.NonNegativeReals,
    )

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def eligibility_rule(instance, participant, car):
        return (
            instance.assignment[participant, car]
            <= instance.interest[participant, car]
        )

    model.eligibility_limits = pyo.Constraint(
        model.participants,
        model.cars,
        rule=eligibility_rule,
    )

    def participant_limit_rule(instance, participant):
        return (
            sum(instance.assignment[participant, car] for car in instance.cars)
            <= instance.participant_capacity
        )

    model.participant_limits = pyo.Constraint(
        model.participants,
        rule=participant_limit_rule,
    )

    def car_limit_rule(instance, car):
        return (
            sum(
                instance.assignment[participant, car]
                for participant in instance.participants
            )
            <= instance.car_capacity
        )

    model.car_limits = pyo.Constraint(
        model.cars,
        rule=car_limit_rule,
    )

    model.total_assignments = pyo.Objective(
        expr=sum(
            model.assignment[participant, car]
            for participant in model.participants
            for car in model.cars
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}