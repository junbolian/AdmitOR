import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preferences = params["preferences"]

    # Normalize the adjacency list into an edge list of (participant, car) pairs.
    edges = []
    for participant_key, car_list in preferences.items():
        p = int(participant_key)
        for c in car_list:
            edges.append((p, int(c)))

    # Build participant and car index sets from the preference structure.
    participants = sorted(set(int(k) for k in preferences.keys()))
    cars = sorted({c for _, c in edges})

    # Deduplicate edges to keep the model well-posed.
    edges = sorted(set(edges))

    model = pyo.ConcreteModel()

    model.participant_set = pyo.Set(initialize=participants)
    model.car_set = pyo.Set(initialize=cars)
    model.edge_set = pyo.Set(initialize=edges, dimen=2)

    model.assign = pyo.Var(model.edge_set, domain=pyo.Binary)

    def objective_rule(m):
        return sum(m.assign[p, c] for (p, c) in m.edge_set)

    model.total_matches = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    # One car per participant (at most one assignment per participant).
    def participant_rule(m, p):
        return sum(m.assign[p, c] for (pp, c) in m.edge_set if pp == p) <= 1

    model.participant_constraint = pyo.Constraint(
        model.participant_set, rule=participant_rule
    )

    # One participant per car (at most one assignment per car).
    def car_rule(m, c):
        return sum(m.assign[p, cc] for (p, cc) in m.edge_set if cc == c) <= 1

    model.car_constraint = pyo.Constraint(model.car_set, rule=car_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_matches))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": str(exc) or "solve_failed"}