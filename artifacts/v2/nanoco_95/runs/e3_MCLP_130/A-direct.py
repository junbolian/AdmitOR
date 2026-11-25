import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    service_range_km = params["service_range_km"]
    demands = params["demands"]
    distances = params["distances"]

    num_clients = len(demands)
    num_sites = len(distances[0])

    model = pyo.ConcreteModel()

    model.CLIENTS = pyo.RangeSet(0, num_clients - 1)
    model.SITES = pyo.RangeSet(0, num_sites - 1)

    # y[j] = 1 if site j is selected
    model.y = pyo.Var(model.SITES, domain=pyo.Binary)

    # z[i] = 1 if community i is covered
    model.z = pyo.Var(model.CLIENTS, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(demands[i] * model.z[i] for i in model.CLIENTS),
        sense=pyo.maximize,
    )

    # Exactly 2 sites selected
    model.exactly_two = pyo.Constraint(
        expr=sum(model.y[j] for j in model.SITES) == 2
    )

    # Coverage linking: community covered only if a selected site is within range
    in_range = {
        (i, j): distances[i][j] <= service_range_km
        for i in range(num_clients)
        for j in range(num_sites)
    }

    def cover_rule(m, i):
        return m.z[i] <= sum(
            m.y[j] for j in m.SITES if in_range[(i, j)]
        )

    model.cover = pyo.Constraint(model.CLIENTS, rule=cover_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}