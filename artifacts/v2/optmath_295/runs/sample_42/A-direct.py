import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    origins = list(range(len(supply)))
    destinations = list(range(len(demand)))
    products = list(range(len(supply[0])))

    model = pyo.ConcreteModel()
    model.O = pyo.Set(initialize=origins)
    model.D = pyo.Set(initialize=destinations)
    model.K = pyo.Set(initialize=products)

    def x_bounds(m, i, j, k):
        return (0, None)
    model.x = pyo.Var(model.O, model.D, model.K, bounds=x_bounds)

    def obj_rule(m):
        return sum(cost[i][j][k] * m.x[i, j, k]
                   for i in m.O for j in m.D for k in m.K)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i, k):
        return sum(m.x[i, j, k] for j in m.D) == supply[i][k]
    model.supply_con = pyo.Constraint(model.O, model.K, rule=supply_rule)

    def demand_rule(m, j, k):
        return sum(m.x[i, j, k] for i in m.O) == demand[j][k]
    model.demand_con = pyo.Constraint(model.D, model.K, rule=demand_rule)

    def cap_rule(m, i, j):
        return sum(m.x[i, j, k] for k in m.K) <= capacity[i][j]
    model.cap_con = pyo.Constraint(model.O, model.D, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}