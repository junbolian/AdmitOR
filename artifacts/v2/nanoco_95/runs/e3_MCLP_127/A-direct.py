import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demands = params["demands"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]
    num_stations_to_install = params["num_stations_to_install"]

    num_zones = len(demands)
    num_sites = len(distance_matrix[0])

    zones = list(range(num_zones))
    sites = list(range(num_sites))

    # coverage[zone][site] = True if zone can be covered by that site
    coverage = {
        (i, j): distance_matrix[i][j] <= coverage_radius
        for i in zones
        for j in sites
    }

    model = pyo.ConcreteModel()

    model.SITES = pyo.Set(initialize=sites)
    model.ZONES = pyo.Set(initialize=zones)

    # y[j] = 1 if site j is selected for installation
    model.y = pyo.Var(model.SITES, domain=pyo.Binary)

    # z[i] = 1 if zone i is covered by at least one selected site
    model.z = pyo.Var(model.ZONES, domain=pyo.Binary)

    # exactly num_stations_to_install sites selected
    model.install_count = pyo.Constraint(
        expr=sum(model.y[j] for j in model.SITES) == num_stations_to_install
    )

    # zone i can only be covered if some covering site is selected
    def coverage_rule(m, i):
        covering_sites = [j for j in sites if coverage[(i, j)]]
        if not covering_sites:
            return m.z[i] == 0
        return m.z[i] <= sum(m.y[j] for j in covering_sites)

    model.coverage_link = pyo.Constraint(model.ZONES, rule=coverage_rule)

    # objective: maximize total demand of covered zones
    model.total_covered_demand = pyo.Objective(
        expr=sum(demands[i] * model.z[i] for i in model.ZONES),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_covered_demand))
    return {"objective": obj_val, "status": "optimal"}