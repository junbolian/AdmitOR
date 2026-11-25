import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    net_demand = params["net_demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    N = 6

    # Build ordered route list: (src, dst) skipping self-routes,
    # and map each route to its column index in the per-source arrays.
    routes = [(i, j) for i in range(N) for j in range(N) if i != j]
    route_index = {r: k for k, r in enumerate(routes)}

    # Build lookup dicts directly, avoiding index-mapping errors.
    cost_map = {}
    cap_map = {}
    for i in range(N):
        dsts = [j for j in range(N) if j != i]
        for k, j in enumerate(dsts):
            cost_map[(i, j)] = cost[i][k]
            cap_map[(i, j)] = capacity[i][k]

    model = pyo.ConcreteModel()

    model.routes = pyo.Set(initialize=routes, dimen=2)
    model.cities = pyo.Set(initialize=range(N))

    model.flow = pyo.Var(model.routes, domain=pyo.NonNegativeReals)

    def cap_rule(m, i, j):
        return m.flow[i, j] <= cap_map[(i, j)]

    model.cap_con = pyo.Constraint(model.routes, rule=cap_rule)

    def balance_rule(m, city):
        inflow = sum(m.flow[i, city] for i in range(N) if i != city)
        outflow = sum(m.flow[city, j] for j in range(N) if j != city)
        return inflow - outflow == net_demand[city]

    model.balance = pyo.Constraint(model.cities, rule=balance_rule)

    def obj_rule(m):
        return sum(cost_map[(i, j)] * m.flow[i, j] for (i, j) in routes)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}