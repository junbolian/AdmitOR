import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demands = params["demands"]
    distances = params["distances"]
    coverage_radius = params["coverage_radius"]
    num_stations = params["num_stations"]

    num_zones = len(demands)
    num_sites = len(distances[0])

    zones = list(range(num_zones))
    sites = list(range(num_sites))

    model = pyo.ConcreteModel()

    model.ZONES = pyo.Set(initialize=zones)
    model.SITES = pyo.Set(initialize=sites)

    model.x = pyo.Var(model.SITES, domain=pyo.Binary)
    model.y = pyo.Var(model.ZONES, domain=pyo.Binary)

    def obj_rule(m):
        return sum(demands[i] * m.y[i] for i in m.ZONES)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def cardinality_rule(m):
        return sum(m.x[j] for j in m.SITES) == num_stations
    model.cardinality = pyo.Constraint(rule=cardinality_rule)

    def cover_reachable_rule(m, i):
        return m.y[i] <= sum(
            m.x[j] for j in m.SITES if distances[i][j] <= coverage_radius
        )
    model.cover_reachable = pyo.Constraint(model.ZONES, rule=cover_reachable_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}