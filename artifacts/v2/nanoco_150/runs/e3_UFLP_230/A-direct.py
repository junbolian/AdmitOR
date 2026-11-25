import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_stops = params["num_stops"]
    num_sites = params["num_sites"]
    installation_costs = params["installation_costs"]
    walking_distances = params["walking_distances"]

    stops = list(range(num_stops))
    sites = list(range(num_sites))

    model = pyo.ConcreteModel()

    model.STOPS = pyo.Set(initialize=stops)
    model.SITES = pyo.Set(initialize=sites)

    model.install_cost = pyo.Param(model.SITES, initialize={j: installation_costs[j] for j in sites}, within=pyo.Reals)
    model.walk = pyo.Param(model.STOPS, model.SITES, initialize={(i, j): walking_distances[i][j] for i in stops for j in sites}, within=pyo.Reals)

    model.y = pyo.Var(model.SITES, domain=pyo.Binary)
    model.x = pyo.Var(model.STOPS, model.SITES, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(model.install_cost[j] * model.y[j] for j in model.SITES)
        + sum(model.walk[i, j] * model.x[i, j] for i in model.STOPS for j in model.SITES),
        sense=pyo.minimize,
    )

    model.assign_once = pyo.Constraint(
        model.STOPS, rule=lambda m, i: sum(m.x[i, j] for j in m.SITES) == 1
    )
    model.link = pyo.Constraint(
        model.STOPS, model.SITES, rule=lambda m, i, j: m.x[i, j] <= m.y[j]
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}