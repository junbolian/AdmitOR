import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Preference matrix structure: 7 participants x 7 cars (structural)
    num_participants = 7
    num_cars = 7

    # Read preference data from params
    pref = params["preference_value"]

    # Build a lookup of allowed (participant, car) pairs from the preference data
    allowed = {}
    for i in range(num_participants):
        for j in range(num_cars):
            allowed[(i, j)] = pref[i][j]

    model = pyo.ConcreteModel()

    # Sets
    model.participants = pyo.Set(initialize=range(num_participants))
    model.cars = pyo.Set(initialize=range(num_cars))

    # Decision variables
    model.assign_var = pyo.Var(model.participants, model.cars, domain=pyo.Binary)

    # Each participant at most one car
    def participant_rule(m, i):
        return sum(m.assign_var[i, j] for j in m.cars) <= 1

    model.participant_constraint = pyo.Constraint(
        model.participants, rule=participant_rule
    )

    # Each car at most one participant
    def car_rule(m, j):
        return sum(m.assign_var[i, j] for i in m.participants) <= 1

    model.car_constraint = pyo.Constraint(model.cars, rule=car_rule)

    # Preference constraints
    def pref_rule(m, i, j):
        return m.assign_var[i, j] <= allowed[(i, j)]

    model.pref_constraint = pyo.Constraint(
        model.participants, model.cars, rule=pref_rule
    )

    # Objective: maximize total assignments
    def obj_rule(m):
        return sum(m.assign_var[i, j] for i in m.participants for j in m.cars)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Solve
    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}