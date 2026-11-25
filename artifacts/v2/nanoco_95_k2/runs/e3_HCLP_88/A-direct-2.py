import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    install_cost = params["facility_installation_cost"]
    demand = params["client_demand"]
    bonus = params["client_premium_bonus"]
    R1 = params["basic_coverage_radius_R1"]
    R2 = params["premium_coverage_radius_R2"]
    dist = params["distance_matrix"]

    n_clients = len(demand)
    n_facilities = len(install_cost)

    clients = list(range(n_clients))
    facilities = list(range(n_facilities))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(facilities, domain=pyo.Binary)
    model.y = pyo.Var(clients, domain=pyo.Binary)

    # Hard constraint: each client covered by at least one installed facility within R1
    def basic_rule(mdl, i):
        return sum(mdl.x[j] for j in facilities if dist[i][j] <= R1) >= 1
    model.basic = pyo.Constraint(clients, rule=basic_rule)

    # Link premium: y[i] <= sum of x[j] for facilities within R2
    def premium_rule(mdl, i):
        return mdl.y[i] <= sum(mdl.x[j] for j in facilities if dist[i][j] <= R2)
    model.premium = pyo.Constraint(clients, rule=premium_rule)

    def net_objective(mdl):
        return (sum(install_cost[j] * mdl.x[j] for j in facilities)
                - sum(bonus[i] * mdl.y[i] for i in clients))
    model.obj = pyo.Objective(rule=net_objective, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}