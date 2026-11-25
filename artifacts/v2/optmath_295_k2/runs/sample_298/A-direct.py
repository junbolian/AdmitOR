import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(10))

    # Build the set of arcs for which a cost is actually provided in params.
    arcs = []
    for i in nodes:
        for j in nodes:
            if i == j:
                continue
            key = f"cost_node{i}_to_node{j}"
            if key in params:
                arcs.append((i, j))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)

    def arc_cost(i, j):
        return params[f"cost_node{i}_to_node{j}"]

    model.obj = pyo.Objective(
        expr=sum(arc_cost(i, j) * model.x[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    def outflow(v):
        return sum(model.x[v, j] for (a, j) in arcs if a == v)

    def inflow(v):
        return sum(model.x[i, v] for (i, b) in arcs if b == v)

    # node_0: net outflow must equal supply_node0
    model.supply_con = pyo.Constraint(
        expr=outflow(0) - inflow(0) == params["supply_node0"]
    )

    # node_9: net inflow must equal demand_node9
    model.demand_con = pyo.Constraint(
        expr=inflow(9) - outflow(9) == params["demand_node9"]
    )

    # intermediate nodes: flow conservation (net = intermediate_net_flow, typically 0)
    def flow_rule(model, v):
        return inflow(v) - outflow(v) == params["intermediate_net_flow"]

    model.flow_con = pyo.Constraint([1, 2, 3, 4, 5, 6, 7, 8], rule=flow_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}