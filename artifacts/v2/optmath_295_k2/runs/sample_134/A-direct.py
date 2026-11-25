import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    num_aircraft_types = int(params["num_aircraft_types"])
    num_routes = int(params["num_routes"])

    A = range(num_aircraft_types)
    R = range(num_routes)

    availability = params["availability"]
    demand = params["demand"]
    cost = params["cost"]
    capability = params["capability"]

    model = pyo.ConcreteModel()

    model.A = pyo.Set(initialize=list(A))
    model.R = pyo.Set(initialize=list(R))
    model.AR = pyo.Set(initialize=[(i, j) for i in A for j in R], dimen=2)

    model.x = pyo.Var(model.AR, domain=pyo.NonNegativeIntegers)

    def cost_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in A for j in R)
    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def avail_rule(m, i):
        return sum(m.x[i, j] for j in R) <= availability[i]
    model.avail_con = pyo.Constraint(model.A, rule=avail_rule)

    def demand_rule(m, j):
        return sum(capability[i][j] * m.x[i, j] for i in A) >= demand[j]
    model.demand_con = pyo.Constraint(model.R, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}