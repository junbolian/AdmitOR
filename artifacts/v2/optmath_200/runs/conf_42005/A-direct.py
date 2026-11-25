import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    net_supply = params["net_supply"]
    cost = params["cost"]
    capacity = params["capacity"]
    num_cities = params["num_cities"]

    model = pyo.ConcreteModel()

    # Directed arcs: origin city i, destination city j, i != j
    city_pairs = [(i, j) for i in range(num_cities) for j in range(num_cities) if i != j]

    model.arcs = pyo.Set(initialize=city_pairs, dimen=2)
    model.cities = pyo.Set(initialize=range(num_cities))

    # Build lookup dicts for cost and capacity indexed by (i, j)
    cost_map = {}
    cap_map = {}
    for i in range(num_cities):
        for j in range(num_cities):
            if i != j:
                cost_map[(i, j)] = cost[i * num_cities + j]
                cap_map[(i, j)] = capacity[i * num_cities + j]

    def flow_bounds(m, i, j):
        return (0, cap_map[(i, j)])

    model.flow = pyo.Var(model.arcs, bounds=flow_bounds)

    def obj_rule(m):
        return sum(cost_map[(i, j)] * m.flow[i, j] for (i, j) in m.arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def balance_rule(m, k):
        outflow = sum(m.flow[k, j] for j in range(num_cities) if j != k)
        inflow = sum(m.flow[i, k] for i in range(num_cities) if i != k)
        return outflow - inflow == net_supply[k]

    model.balance = pyo.Constraint(model.cities, rule=balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}