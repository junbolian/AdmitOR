import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply_demand = list(params["supply_demand"])
    cost_matrix = list(params["cost_matrix"])
    capacity_matrix = list(params["capacity_matrix"])
    num_cities = int(params["num_cities"])

    model = pyo.ConcreteModel()
    model.cities = pyo.RangeSet(0, num_cities - 1)

    # Number of off-diagonal arcs is N*(N-1)
    num_arcs = num_cities * (num_cities - 1)
    if len(cost_matrix) < num_arcs or len(capacity_matrix) < num_arcs:
        raise ValueError("cost_matrix/capacity_matrix too short for given num_cities")

    arcs = [(i, j) for i in range(num_cities) for j in range(num_cities) if i != j]
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    cost = {}
    cap = {}
    k = 0
    for i in range(num_cities):
        for j in range(num_cities):
            if i != j:
                cost[(i, j)] = cost_matrix[k]
                cap[(i, j)] = capacity_matrix[k]
                k += 1

    model.cost = pyo.Param(model.arcs, initialize=cost)
    model.capacity = pyo.Param(model.arcs, initialize=cap)

    def flow_bounds(mdl, i, j):
        return (0, mdl.capacity[i, j])

    model.flow = pyo.Var(model.arcs, bounds=flow_bounds)

    def objective_rule(mdl):
        return sum(mdl.cost[i, j] * mdl.flow[i, j] for (i, j) in mdl.arcs)

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def balance_rule(mdl, c):
        inflow = sum(mdl.flow[i, c] for (i, j) in mdl.arcs if j == c)
        outflow = sum(mdl.flow[c, j] for (i, j) in mdl.arcs if i == c)
        return inflow - outflow == supply_demand[c]

    model.balance = pyo.Constraint(model.cities, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}