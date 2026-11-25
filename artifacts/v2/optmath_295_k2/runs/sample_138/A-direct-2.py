import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    n = 6
    net_demand = params["net_demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    # Build ordered route list: (source, dest, cost, capacity)
    routes = []
    for i in range(n):
        dests = [j for j in range(n) if j != i]
        for k, j in enumerate(dests):
            routes.append((i, j, cost[i][k], capacity[i][k]))

    model = pyo.ConcreteModel()

    route_set = list(range(len(routes)))
    model.route_set = pyo.Set(initialize=route_set, ordered=True)

    # flow variables
    def flow_bounds(m, r):
        return (0, routes[r][3])
    model.flow = pyo.Var(model.route_set, bounds=flow_bounds)

    # Objective
    def obj_rule(m):
        return sum(routes[r][2] * m.flow[r] for r in m.route_set)
    model.obj_expr = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Flow balance per city
    # net inflow - net outflow = net_demand
    # flow r goes from routes[r][0] to routes[r][1]
    city_list = list(range(n))

    def balance_rule(m, c):
        inflow = sum(m.flow[r] for r in m.route_set if routes[r][1] == c)
        outflow = sum(m.flow[r] for r in m.route_set if routes[r][0] == c)
        return inflow - outflow == net_demand[c]

    model.balance = pyo.Constraint(city_list, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj_expr))
    return {"objective": obj_val, "status": "optimal"}