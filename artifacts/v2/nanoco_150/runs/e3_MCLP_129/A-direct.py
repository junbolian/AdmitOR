import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_towers = int(params["num_towers_to_select"])
    radius = params["service_radius_km"]
    demands = params["community_demands"]
    dist = params["distance_matrix"]

    n_comm = len(demands)
    n_sites = len(dist[0])

    # Eligibility: community i covered by site j if within radius
    eligible = [(i, j) for i in range(n_comm) for j in range(n_sites)
                if dist[i][j] <= radius]

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, n_comm - 1)
    model.J = pyo.RangeSet(0, n_sites - 1)

    model.x = pyo.Var(model.J, domain=pyo.Binary)  # open tower at site j
    model.y = pyo.Var(model.I, domain=pyo.Binary)  # community i connected

    # Exactly num_towers sites activated
    model.card = pyo.Constraint(expr=sum(model.x[j] for j in model.J) == num_towers)

    # Community can be connected only if some eligible site is open
    model.cover = pyo.ConstraintList()
    for i in range(n_comm):
        eligible_sites = [j for (ii, j) in eligible if ii == i]
        model.cover.add(model.y[i] <= sum(model.x[j] for j in eligible_sites))

    model.obj = pyo.Objective(
        expr=sum(demands[i] * model.y[i] for i in model.I),
        sense=pyo.maximize
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}