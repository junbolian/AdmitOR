import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Structural constants
    num_participants = 4
    num_cars = 4
    participants = list(range(num_participants))
    cars = list(range(num_cars))

    # Read data from params
    interest = {
        0: params["participant_car_interest_p0"],
        1: params["participant_car_interest_p1"],
        2: params["participant_car_interest_p2"],
        3: params["participant_car_interest_p3"],
    }
    obj_coeffs = params["assignment_objective_coefficients"]
    participant_cap = params["participant_capacity"]
    car_cap = params["car_capacity"]

    model = pyo.ConcreteModel()

    model.participants = pyo.Set(initialize=participants)
    model.cars = pyo.Set(initialize=cars)

    model.assign = pyo.Var(
        model.participants, model.cars, domain=pyo.Binary
    )

    # Objective: maximize weighted sum of assignments
    def obj_rule(m):
        return sum(
            obj_coeffs[i * num_cars + j] * m.assign[i, j]
            for i in m.participants
            for j in m.cars
        )

    model.total_assignments = pyo.Objective(
        rule=obj_rule, sense=pyo.maximize
    )

    # Constraint: only assign cars the participant is interested in
    def interest_rule(m, i, j):
        if interest[i][j] == 0:
            return m.assign[i, j] == 0
        return pyo.Constraint.Skip

    model.interest_constraint = pyo.Constraint(
        model.participants, model.cars, rule=interest_rule
    )

    # Constraint: each participant assigned at most participant_cap cars
    def participant_rule(m, i):
        return sum(m.assign[i, j] for j in m.cars) <= participant_cap

    model.participant_constraint = pyo.Constraint(
        model.participants, rule=participant_rule
    )

    # Constraint: each car assigned at most car_cap participants
    def car_rule(m, j):
        return sum(m.assign[i, j] for i in m.participants) <= car_cap

    model.car_constraint = pyo.Constraint(model.cars, rule=car_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_assignments))
    return {"objective": obj_val, "status": "optimal"}