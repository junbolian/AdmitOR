import gurobipy as gp

def solve(params):
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]
    demands = params["demands"]

    num_nodes = 8
    num_commodities = 2

    undirected_edges = [
        [0, 1], [0, 3], [0, 5], [0, 6], [0, 7],
        [1, 2], [1, 5], [1, 6],
        [2, 3], [2, 6],
        [3, 4],
        [4, 5], [4, 6], [4, 7],
        [5, 6], [5, 7],
        [6, 7],
    ]

    commodities = [
        {"source": 3, "sink": 7},
        {"source": 1, "sink": 5},
    ]

    arcs = []
    for i, j in undirected_edges:
        arcs.append((i, j))
        arcs.append((j, i))
    num_arcs = len(arcs)

    if len(arc_capacities) != num_arcs:
        raise ValueError("arc_capacities length does not match number of arcs")
    if len(arc_unit_costs) != num_arcs:
        raise ValueError("arc_unit_costs length does not match number of arcs")
    if len(demands) != num_commodities:
        raise ValueError("demands length does not match number of commodities")

    outgoing = {n: [] for n in range(num_nodes)}
    incoming = {n: [] for n in range(num_nodes)}
    for arc_idx, (i, j) in enumerate(arcs):
        outgoing[i].append(arc_idx)
        incoming[j].append(arc_idx)

    model = gp.Model("multi_commodity_power_flow")
    model.setParam("OutputFlag", 0)

    flows = model.addVars(num_commodities, num_arcs, lb=0.0, vtype=gp.GRB.CONTINUOUS)

    for k, commodity in enumerate(commodities):
        source = commodity["source"]
        sink = commodity["sink"]
        demand = demands[k]
        for n in range(num_nodes):
            if n == source:
                net = demand
            elif n == sink:
                net = -demand
            else:
                net = 0.0
            model.addConstr(
                gp.quicksum(flows[k, a] for a in outgoing[n])
                - gp.quicksum(flows[k, a] for a in incoming[n])
                == net
            )

    for a in range(num_arcs):
        model.addConstr(
            gp.quicksum(flows[k, a] for k in range(num_commodities)) <= arc_capacities[a]
        )

    model.setObjective(
        gp.quicksum(
            arc_unit_costs[a] * gp.quicksum(flows[k, a] for k in range(num_commodities))
            for a in range(num_arcs)
        ),
        gp.GRB.MINIMIZE,
    )

    model.optimize()

    if model.status == gp.GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == gp.GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.status == gp.GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    if model.status == gp.GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    return {"objective": None, "status": "failed"}