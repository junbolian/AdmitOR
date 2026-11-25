import gurobipy as gp
from gurobipy import GRB

def solve(params):
    arc_capacities = params["arc_capacities"]
    arc_costs = params["arc_costs"]
    commodity_sources = params["commodity_sources"]
    commodity_sinks = params["commodity_sinks"]
    commodity_demands = params["commodity_demands"]

    arcs = [
        (0,1),(1,0),(0,4),(4,0),(1,2),(2,1),(1,5),(5,1),
        (2,3),(3,2),(2,6),(6,2),(3,4),(4,3),(3,9),(9,3),
        (4,5),(5,4),(4,6),(6,4),(5,6),(6,5),(5,7),(7,5),
        (6,7),(7,6),(7,8),(8,7),(8,9),(9,8)
    ]
    num_arcs = len(arcs)
    num_nodes = 10
    num_commodities = 2

    arc_cap = {arcs[i]: arc_capacities[i] for i in range(num_arcs)}
    arc_cost = {arcs[i]: arc_costs[i] for i in range(num_arcs)}

    # Build adjacency structures
    out_arcs = {n: [] for n in range(num_nodes)}
    in_arcs  = {n: [] for n in range(num_nodes)}
    for (u, v) in arcs:
        out_arcs[u].append((u, v))
        in_arcs[v].append((u, v))

    model = gp.Model("mcf")
    model.setParam("OutputFlag", 0)

    # Decision variables: flow[k][arc]
    flow = {}
    for k in range(num_commodities):
        for arc in arcs:
            flow[(k, arc)] = model.addVar(lb=0.0, name=f"f_{k}_{arc[0]}_{arc[1]}")

    model.update()

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(arc_cost[arc] * flow[(k, arc)]
                    for k in range(num_commodities)
                    for arc in arcs),
        GRB.MINIMIZE
    )

    # Flow conservation constraints
    for k in range(num_commodities):
        src = commodity_sources[k]
        snk = commodity_sinks[k]
        dem = commodity_demands[k]
        for node in range(num_nodes):
            out_flow = gp.quicksum(flow[(k, arc)] for arc in out_arcs[node])
            in_flow  = gp.quicksum(flow[(k, arc)] for arc in in_arcs[node])
            if node == src:
                model.addConstr(out_flow - in_flow == dem,
                                name=f"balance_k{k}_n{node}")
            elif node == snk:
                model.addConstr(in_flow - out_flow == dem,
                                name=f"balance_k{k}_n{node}")
            else:
                model.addConstr(out_flow - in_flow == 0,
                                name=f"balance_k{k}_n{node}")

    # Shared capacity constraints
    for arc in arcs:
        model.addConstr(
            gp.quicksum(flow[(k, arc)] for k in range(num_commodities)) <= arc_cap[arc],
            name=f"cap_{arc[0]}_{arc[1]}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}