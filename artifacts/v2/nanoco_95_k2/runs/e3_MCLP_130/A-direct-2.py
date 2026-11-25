import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demands = params["demands"]
    threshold = params["coverage_threshold_km"]
    num_sites = params["num_sites_to_deploy"]
    dist = params["distance_matrix"]

    n_communities = len(demands)
    n_sites = len(dist[0])

    model = pyo.ConcreteModel()

    model.communities = pyo.RangeSet(0, n_communities - 1)
    model.sites = pyo.RangeSet(0, n_sites - 1)

    model.x = pyo.Var(model.sites, within=pyo.Binary)
    model.y = pyo.Var(model.communities, within=pyo.Binary)

    def cover_rule(m, i):
        return m.y[i] <= sum(m.x[j] for j in m.sites if dist[i][j] <= threshold)
    model.cover = pyo.Constraint(model.communities, rule=cover_rule)

    model.site_count = pyo.Constraint(expr=sum(model.x[j] for j in model.sites) == num_sites)

    model.objective = pyo.Objective(
        expr=sum(demands[i] * model.y[i] for i in model.communities),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}