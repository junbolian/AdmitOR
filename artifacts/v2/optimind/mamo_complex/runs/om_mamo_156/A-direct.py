import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    locations = [1, 2, 3, 4, 5]

    # Undirected pairs with i < j: cars may move in either direction.
    pairs = [(1, 2), (1, 3), (1, 4), (1, 5),
             (2, 3), (2, 4), (2, 5),
             (3, 4), (3, 5),
             (4, 5)]

    model = pyo.ConcreteModel()

    model.L = pyo.Set(initialize=locations)
    model.P = pyo.Set(initialize=pairs, dimen=2)

    # Cost per unit flow for both directions on each pair.
    cost_data = {}
    for (i, j) in pairs:
        c = params["cost_%d_%d" % (i, j)]
        cost_data[(i, j)] = c
        cost_data[(j, i)] = c

    supply_data = {k: params["supply_%d" % k] for k in locations}
    demand_data = {k: params["demand_%d" % k] for k in locations}
    model.supply = pyo.Param(model.L, initialize=supply_data, mutable=False)
    model.demand = pyo.Param(model.L, initialize=demand_data, mutable=False)

    # Decision variables: flow along each ordered movement.
    model.x = pyo.Var(model.P, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost_data[(i, j)] * (m.x[i, j] + m.x[j, i]) for (i, j) in pairs)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Flow balance: net outflow equals supply minus demand at each location.
    def balance_rule(m, k):
        outflow = sum(m.x[i, j] for (i, j) in pairs if i == k)
        outflow += sum(m.x[j, i] for (i, j) in pairs if j == k)
        inflow = sum(m.x[i, j] for (i, j) in pairs if j == k)
        inflow += sum(m.x[j, i] for (i, j) in pairs if i == k)
        return outflow - inflow == m.supply[k] - m.demand[k]
    model.balance = pyo.Constraint(model.L, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}