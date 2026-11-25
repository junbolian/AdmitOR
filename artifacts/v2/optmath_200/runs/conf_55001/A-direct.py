import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_participants = 5
    n_cars = 5
    participants = list(range(n_participants))
    cars = list(range(n_cars))

    preference = [
        [params["preference_p0"][k] for k in range(n_cars)],
        [params["preference_p1"][k] for k in range(n_cars)],
        [params["preference_p2"][k] for k in range(n_cars)],
        [params["preference_p3"][k] for k in range(n_cars)],
        [params["preference_p4"][k] for k in range(n_cars)],
    ]

    participant_capacity = [
        params["participant_0_capacity"],
        params["participant_1_capacity"],
        params["participant_2_capacity"],
        params["participant_3_capacity"],
        params["participant_4_capacity"],
    ]

    car_capacity = [
        params["car_0_capacity"],
        params["car_1_capacity"],
        params["car_2_capacity"],
        params["car_3_capacity"],
        params["car_4_capacity"],
    ]

    weight = params["objective_weight_per_assignment"]

    allowed_pairs = [
        (i, j) for i in participants for j in cars if preference[i][j] == 1
    ]

    allowed_set = set(allowed_pairs)

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=participants)
    model.C = pyo.Set(initialize=cars)
    model.A = pyo.Set(dimen=2, initialize=allowed_pairs)

    model.x = pyo.Var(model.A, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(weight * model.x[i, j] for (i, j) in allowed_pairs),
        sense=pyo.maximize,
    )

    def participant_rule(mdl, i):
        return sum(
            mdl.x[i, j] for j in cars if (i, j) in allowed_set
        ) <= participant_capacity[i]

    model.participant_cap = pyo.Constraint(model.P, rule=participant_rule)

    def car_rule(mdl, j):
        return sum(
            mdl.x[i, j] for i in participants if (i, j) in allowed_set
        ) <= car_capacity[j]

    model.car_cap = pyo.Constraint(model.C, rule=car_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}