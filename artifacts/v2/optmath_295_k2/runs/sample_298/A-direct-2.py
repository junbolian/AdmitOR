import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(10))
    intermediate_nodes = list(range(1, 9))

    # Build cost dict only for arcs that exist in params.
    # The data provides costs for pairs (i, j) with i in 0..9 and j in 0..9,
    # but only a subset is guaranteed. We collect every arc (i, j) for which
    # a cost entry is present, then verify the required ones exist.
    cost = {}
    prefix = "cost_node"
    mid = "_to_node"
    for key, val in params.items():
        if key.startswith(prefix) and mid in key:
            try:
                i_str, j_str = key[len(prefix):].split(mid)
                i = int(i_str)
                j = int(j_str)
            except (ValueError, AttributeError):
                continue
            if i != j:
                cost[(i, j)] = val

    arcs = list(cost.keys())

    # Net outflow requirement per node
    net = {}
    net[0] = params["supply_node0"]
    net[9] = -params["demand_node9"]
    for k in intermediate_nodes:
        net[k] = params["intermediate_net_flow"]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)

    def balance_rule(m, k):
        outflow = sum(m.x[(k, j)] for (i, j) in arcs if i == k)
        inflow = sum(m.x[(i, k)] for (i, j) in arcs if j == k)
        return outflow - inflow == net[k]

    model.balance = pyo.Constraint(nodes, rule=balance_rule)

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[(i, j)] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}