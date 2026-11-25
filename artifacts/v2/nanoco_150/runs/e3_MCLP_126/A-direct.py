import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    coverage_radius = params["coverage_radius"]
    num_stations = params["num_stations"]
    distance_matrix = params["distance_matrix"]

    n_clients = len(demand)
    n_facilities = len(distance_matrix[0])

    clients = range(n_clients)
    facilities = range(n_facilities)

    # Which facilities can cover each client
    covering = {
        i: [j for j in facilities if distance_matrix[i][j] <= coverage_radius]
        for i in clients
    }

    model = pyo.ConcreteModel()

    model.x = pyo.Var(facilities, domain=pyo.Binary)
    model.y = pyo.Var(clients, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(demand[i] * model.y[i] for i in clients),
        sense=pyo.maximize,
    )

    model.card = pyo.Constraint(
        expr=sum(model.x[j] for j in facilities) == num_stations
    )

    def cover_rule(m, i):
        return m.y[i] <= sum(m.x[j] for j in covering[i]) if covering[i] else m.y[i] <= 0

    model.cover = pyo.Constraint(clients, rule=cover_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}