import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_districts = 27
    n_sites = 10

    districts = list(range(1, n_districts + 1))
    sites = list(range(1, n_sites + 1))

    install_cost = params["installation_cost"]
    demand = params["demand"]
    distance = params["distance"]
    grant_revenue = params["grant_revenue"]
    coverage_radius = params["coverage_radius"]
    precision_radius = params["precision_radius"]

    # Coverage: district i can be served by site j if distance <= coverage_radius
    covers = {
        (i, j): (distance[i - 1][j - 1] <= coverage_radius)
        for i in districts for j in sites
    }
    # Precision: district i is precision-monitored by site j if distance <= precision_radius
    precise = {
        (i, j): (distance[i - 1][j - 1] <= precision_radius)
        for i in districts for j in sites
    }

    model = pyo.ConcreteModel()

    model.J = pyo.Set(initialize=sites)
    model.I = pyo.Set(initialize=districts)

    model.y = pyo.Var(model.J, domain=pyo.Binary)
    model.z = pyo.Var(model.I, domain=pyo.Binary)

    model.install_cost = pyo.Param(model.J, initialize={j: install_cost[j - 1] for j in sites})
    model.grant = pyo.Param(model.I, initialize={i: grant_revenue[i - 1] for i in districts})

    # Objective: minimize installation cost - grant revenue
    model.obj = pyo.Objective(
        expr=sum(model.install_cost[j] * model.y[j] for j in model.J)
        - sum(model.grant[i] * model.z[i] for i in model.I),
        sense=pyo.minimize,
    )

    # Every district must be covered by at least one deployed station
    model.coverage = pyo.Constraint(model.I, rule=lambda m, i: sum(
        m.y[j] for j in m.J if covers[(i, j)]
    ) >= 1)

    # A district can only be precision-monitored if a precise site is deployed
    def precision_rule(m, i):
        precise_sites = [j for j in m.J if precise[(i, j)]]
        if not precise_sites:
            return pyo.Constraint.Skip
        return m.z[i] <= sum(m.y[j] for j in precise_sites)

    model.precision = pyo.Constraint(model.I, rule=precision_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}