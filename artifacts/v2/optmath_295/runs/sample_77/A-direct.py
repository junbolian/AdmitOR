import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    aircraft = list(range(8))
    routes = list(range(8))

    availability = params["aircraft_availability"]
    demand = params["route_demand"]
    cost = params["cost_matrix"]
    cap = params["capacity_matrix"]

    model = pyo.ConcreteModel()

    model.A = pyo.Set(initialize=aircraft)
    model.R = pyo.Set(initialize=routes)

    model.x = pyo.Var(model.A, model.R, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.A for j in m.R)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def avail_rule(m, i):
        return sum(m.x[i, j] for j in m.R) <= availability[i]

    model.avail_con = pyo.Constraint(model.A, rule=avail_rule)

    def demand_rule(m, j):
        return sum(cap[i][j] * m.x[i, j] for i in m.A) >= demand[j]

    model.demand_con = pyo.Constraint(model.R, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}