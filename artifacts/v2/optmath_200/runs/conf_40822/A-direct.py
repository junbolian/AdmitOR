import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Read parameters from the params dict
    allowance = params["assignment_allowance"]
    part_cap = params["participant_assignment_capacity"]
    car_cap = params["car_assignment_capacity"]

    # Structural constants (index structure only)
    participants = list(range(len(allowance)))          # rows of allowance
    cars = list(range(len(allowance[0])))               # columns of allowance

    model = pyo.ConcreteModel()

    # Decision variables: x[i, j] = 1 if participant i assigned to car j
    model.x = pyo.Var(participants, cars, domain=pyo.Binary)

    # Objective: maximize total number of successful assignments
    model.total_assignments = pyo.Objective(
        expr=sum(model.x[i, j] for i in participants for j in cars),
        sense=pyo.maximize,
    )

    # Constraint 1: each participant assigned to at most part_cap[i] cars
    def participant_rule(mdl, i):
        return sum(mdl.x[i, j] for j in cars) <= part_cap[i]

    model.participant_limit = pyo.Constraint(participants, rule=participant_rule)

    # Constraint 2: each car assigned to at most car_cap[j] participants
    def car_rule(mdl, j):
        return sum(mdl.x[i, j] for i in participants) <= car_cap[j]

    model.car_limit = pyo.Constraint(cars, rule=car_rule)

    # Constraint 3: assignments must respect participant preferences
    def preference_rule(mdl, i, j):
        if allowance[i][j] == 0:
            return mdl.x[i, j] == 0
        return pyo.Constraint.Skip

    model.preferences = pyo.Constraint(
        participants, cars, rule=preference_rule
    )

    # Solve with HiGHS via Appsi
    Highs().solve(model)

    # Success determined solely by retrievability of the objective value
    obj_val = float(pyo.value(model.total_assignments))
    return {"objective": obj_val, "status": "optimal"}