import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = int(params["num_participants"])
    num_cars = int(params["num_cars"])
    assignment_value = params["assignment_value"]

    # Build the set of allowed (participant, car) pairs from preference params.
    allowed = set()
    any_vals = {}
    for key, val in params.items():
        if key.startswith("preference_p") and key.endswith("_any"):
            p_str = key[len("preference_p"):-len("_any")]
            any_vals[int(p_str)] = val
        elif key.startswith("preference_p") and "_c" in key:
            body = key[len("preference_p"):]
            p_str, c_str = body.split("_c")
            if val != 0:
                allowed.add((int(p_str), int(c_str)))

    for p, val in any_vals.items():
        if val != 0:
            for c in range(num_cars):
                allowed.add((p, c))

    valid_pairs = sorted(
        (p, c) for (p, c) in allowed
        if 0 <= p < num_participants and 0 <= c < num_cars
    )

    model = pyo.ConcreteModel()
    model.PARTICIPANTS = pyo.RangeSet(0, num_participants - 1)
    model.CARS = pyo.RangeSet(0, num_cars - 1)
    model.VALID = pyo.Set(initialize=valid_pairs, dimen=2)

    model.x = pyo.Var(model.VALID, domain=pyo.Binary)

    # Precompute per-participant and per-car allowed car/participant lists
    # so constraint rules never resolve to a trivial Boolean when empty.
    cars_for_participant = {p: [] for p in model.PARTICIPANTS}
    participants_for_car = {c: [] for c in model.CARS}
    for (p, c) in valid_pairs:
        cars_for_participant[p].append(c)
        participants_for_car[c].append(p)

    def obj_rule(mdl):
        return assignment_value * sum(mdl.x[p, c] for (p, c) in mdl.VALID)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def participant_rule(mdl, p):
        terms = [mdl.x[p, c] for c in cars_for_participant[p]]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1

    model.participant_con = pyo.Constraint(model.PARTICIPANTS, rule=participant_rule)

    def car_rule(mdl, c):
        terms = [mdl.x[p, c] for p in participants_for_car[c]]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1

    model.car_con = pyo.Constraint(model.CARS, rule=car_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}