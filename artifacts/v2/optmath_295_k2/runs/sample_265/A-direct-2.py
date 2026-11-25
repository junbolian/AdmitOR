import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    edge_cost = params["edge_cost"]
    supply_node_0 = params["supply_node_0"]
    demand_node_7 = params["demand_node_7"]

    nodes = list(range(8))

    # Build the list of ordered pairs (excluding self-loops) in row-major order
    pairs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    model.PAIRS = pyo.Set(initialize=pairs, dimen=2)

    cost = {(i, j): edge_cost[k] for k, (i, j) in enumerate(pairs)}

    model.c = pyo.Param(model.PAIRS, initialize=cost)

    # Binary routing decision
    model.x = pyo.Var(model.PAIRS, domain=pyo.Binary)

    # Flow on each route (continuous, bounded by binary)
    model.f = pyo.Var(model.PAIRS, domain=pyo.NonNegativeReals, bounds=(0, 1))

    # Link flow to binary: flow <= binary decision
    def link_rule(m, i, j):
        return m.f[i, j] <= m.x[i, j]
    model.link = pyo.Constraint(model.PAIRS, rule=link_rule)

    # Flow balance constraints
    def balance_rule(m, k):
        outflow = sum(m.f[k, j] for j in nodes if j != k)
        inflow = sum(m.f[i, k] for i in nodes if i != k)
        if k == 0:
            return outflow - inflow == supply_node_0
        elif k == 7:
            return inflow - outflow == demand_node_7
        else:
            return inflow - outflow == 0
    model.balance = pyo.Constraint(nodes, rule=balance_rule)

    # Objective: minimize total cost
    model.obj = pyo.Objective(
        expr=sum(model.c[i, j] * model.f[i, j] for (i, j) in model.PAIRS),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}