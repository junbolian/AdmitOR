import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demands = params["demands"]
    coverage_radius = params["coverage_radius"]
    travel_times = params["travel_times"]

    num_communities = len(demands)
    num_depots = len(travel_times[0])

    # Determine which (community, depot) pairs are covered within radius
    covered = [
        [1 if travel_times[i][j] <= coverage_radius else 0 for j in range(num_depots)]
        for i in range(num_communities)
    ]

    model = pyo.ConcreteModel()

    model.communities = pyo.RangeSet(0, num_communities - 1)
    model.depots = pyo.RangeSet(0, num_depots - 1)

    # y[j] = 1 if depot j is activated
    model.y = pyo.Var(model.depots, domain=pyo.Binary)

    # z[i] = 1 if community i is served
    model.z = pyo.Var(model.communities, domain=pyo.Binary)

    # Objective: maximize total covered demand
    def obj_rule(mdl):
        return sum(demands[i] * mdl.z[i] for i in mdl.communities)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Exactly 4 depots activated
    model.num_depots_constraint = pyo.Constraint(
        expr=sum(model.y[j] for j in model.depots) == 4
    )

    # Community i can be served only if at least one covering depot is activated
    def coverage_rule(mdl, i):
        return mdl.z[i] <= sum(
            covered[i][j] * mdl.y[j] for j in mdl.depots
        )

    model.coverage_constraint = pyo.Constraint(
        model.communities, rule=coverage_rule
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}