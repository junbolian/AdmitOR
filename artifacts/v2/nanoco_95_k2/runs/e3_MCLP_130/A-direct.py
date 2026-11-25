import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demands = params["demands"]
    threshold = params["coverage_threshold_km"]
    p = params["num_sites_to_deploy"]
    dist = params["distance_matrix"]

    num_communities = len(demands)
    num_sites = len(dist[0])

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, num_communities - 1)
    model.J = pyo.RangeSet(0, num_sites - 1)

    model.y = pyo.Var(model.J, domain=pyo.Binary)
    model.z = pyo.Var(model.I, domain=pyo.Binary)

    def obj_rule(m):
        return sum(demands[i] * m.z[i] for i in m.I)

    model.total_reach = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    model.deploy = pyo.Constraint(expr=sum(model.y[j] for j in model.J) == p)

    model.link = pyo.Constraint(
        model.I,
        rule=lambda m, i: m.z[i] <= sum(
            m.y[j] for j in m.J if dist[i][j] <= threshold
        ),
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_reach))
    return {"objective": obj_val, "status": "optimal"}