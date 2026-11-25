import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    aircraft = list(range(5))
    routes = list(range(6))

    availability = params["aircraft_availability"]
    demand = params["route_demand"]
    capacity_coeff = params["capacity_coeff"]
    operational_cost = params["operational_cost"]

    model = pyo.ConcreteModel()

    model.A = pyo.Set(initialize=aircraft)
    model.R = pyo.Set(initialize=routes)

    model.x = pyo.Var(model.A, model.R, domain=pyo.NonNegativeIntegers)

    def cost_rule(m):
        return sum(operational_cost[i][j] * m.x[i, j] for i in m.A for j in m.R)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def avail_rule(m, i):
        return sum(m.x[i, j] for j in m.R) <= availability[i]

    model.avail_con = pyo.Constraint(model.A, rule=avail_rule)

    def demand_rule(m, j):
        return sum(capacity_coeff[i][j] * m.x[i, j] for i in m.A) >= demand[j]

    model.demand_con = pyo.Constraint(model.R, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}