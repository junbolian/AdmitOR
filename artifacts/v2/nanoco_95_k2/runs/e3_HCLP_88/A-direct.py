import pyomo.environ as pyo
import math

def solve(params):
    n_clients = 21
    n_facilities = 15

    install_cost = params["facility_installation_cost"]
    demand = params["client_demand"]
    bonus = params["client_premium_bonus"]
    R1 = params["basic_coverage_radius_R1"]
    R2 = params["premium_coverage_radius_R2"]
    dist = params["distance_matrix"]

    clients = list(range(1, n_clients + 1))
    facilities = list(range(1, n_facilities + 1))

    # Basic coverage: household i can be served by facility j if dist[i][j] <= R1
    basic_cover = {i: [j for j in facilities if dist[i-1][j-1] <= R1] for i in clients}
    # Premium coverage: household i gets premium from facility j if dist[i][j] <= R2
    premium_cover = {i: [j for j in facilities if dist[i-1][j-1] <= R2] for i in clients}

    model = pyo.ConcreteModel()

    model.CLIENTS = pyo.Set(initialize=clients)
    model.FACILITIES = pyo.Set(initialize=facilities)

    model.x = pyo.Var(model.FACILITIES, domain=pyo.Binary)   # install facility
    model.y = pyo.Var(model.CLIENTS, domain=pyo.Binary)      # household gets premium
    model.z = pyo.Var(model.CLIENTS, model.FACILITIES, domain=pyo.Binary)  # basic assignment

    # Objective: net cost = installation costs - premium bonuses
    def obj_rule(m):
        return sum(install_cost[j-1] * m.x[j] for j in m.FACILITIES) \
             - sum(bonus[i-1] * m.y[i] for i in m.CLIENTS)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Hard SLA: every household served by at least one installed NAP within R1
    def basic_rule(m, i):
        return sum(m.z[i, j] for j in basic_cover[i]) >= 1
    model.basic_coverage = pyo.Constraint(model.CLIENTS, rule=basic_rule)

    # Assignment only to installed facilities (link basic assignment to x)
    def assign_rule(m, i, j):
        if j in basic_cover[i]:
            return m.z[i, j] <= m.x[j]
        else:
            return pyo.Constraint.Skip
    model.assign = pyo.Constraint(model.CLIENTS, model.FACILITIES, rule=assign_rule)

    # Premium link: y_i <= sum of x_j for facilities within R2
    def premium_rule(m, i):
        if len(premium_cover[i]) == 0:
            return m.y[i] == 0
        return m.y[i] <= sum(m.x[j] for j in premium_cover[i])
    model.premium = pyo.Constraint(model.CLIENTS, rule=premium_rule)

    from pyomo.contrib.appsi.solvers.highs import Highs
    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}