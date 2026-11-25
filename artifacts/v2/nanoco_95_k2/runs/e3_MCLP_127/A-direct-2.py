import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demands = params["demands"]
    distances = params["distances"]
    coverage_radius = params["coverage_radius"]
    num_stations = params["num_stations"]

    num_zones = len(demands)
    num_sites = len(distances[0])

    model = pyo.ConcreteModel()

    model.ZONES = pyo.RangeSet(0, num_zones - 1)
    model.SITES = pyo.RangeSet(0, num_sites - 1)

    model.install = pyo.Var(model.SITES, domain=pyo.Binary)
    model.covered = pyo.Var(model.ZONES, domain=pyo.Binary)

    model.cardinality = pyo.Constraint(
        expr=sum(model.install[j] for j in model.SITES) == num_stations
    )

    def coverage_rule(mdl, i):
        reachable = [j for j in mdl.SITES if distances[i][j] <= coverage_radius]
        return mdl.covered[i] <= sum(mdl.install[j] for j in reachable)

    model.coverage = pyo.Constraint(model.ZONES, rule=coverage_rule)

    model.obj = pyo.Objective(
        expr=sum(demands[i] * model.covered[i] for i in model.ZONES),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}