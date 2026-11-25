import gurobipy as gp
from gurobipy import GRB

def solve(params):
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]
    demands = params["demands"]
    num_nodes = params["num_nodes"]
    num_commodities = params["num_commodities"]

    # Define directed arcs in fixed order matching capacities/costs
    arcs = [
        (0,1),(1,0),(0,3),(3,0),(0,5),(5,0),(0,6),(6,0),(0,7),(7,0),
        (1,2),(2,1),(1,5),(5,1),(1,6),(6,1),(2,3),(3,2),(2,6),(6,2),
        (3,4),(4,3),(4,5),(5,4),(4,6),(6,4),(4,7),(7,4),(5,6),(6,5),
        (5,7),(7,5),(6,7),(7,6)
    ]

    # Commodities: (source, sink, demand), 0-indexed
    commodities_def = [
        (3, 7, demands[0]),  # Commodity 1
        (1, 5, demands[1]),  # Commodity 2
    ]

    arc_cap = {arcs[i]: arc_capacities[i] for i in range(len(arcs))}
    arc_cost = {arcs[i]: arc_unit_costs[i] for i in range(len(arcs))}

    # Build adjacency: outgoing and incoming arcs per node
    nodes = list(range(num_nodes))
    commodities = list(range(num_commodities))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Flow variables: x[k, i, j] = flow of commodity k on arc (i,j)
    x = {}
    for k in commodities:
        for arc in arcs:
            x[k, arc] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS)

    model.update()

    # Objective: minimize total transmission cost
    model.setObjective(
        gp.quicksum(arc_cost[arc] * x[k, arc] for k in commodities for arc in arcs),
        GRB.MINIMIZE
    )

    # Flow balance constraints
    for k in commodities:
        src, snk, demand = commodities_def[k]
        for node in nodes:
            outflow = gp.quicksum(x[k, (node, j)] for (i, j) in arcs if i == node)
            inflow  = gp.quicksum(x[k, (i, node)] for (i, j) in arcs if j == node)
            if node == src:
                model.addConstr(outflow - inflow == demand)
            elif node == snk:
                model.addConstr(inflow - outflow == demand)
            else:
                model.addConstr(outflow - inflow == 0)

    # Capacity constraints: sum over commodities <= arc capacity
    for arc in arcs:
        model.addConstr(
            gp.quicksum(x[k, arc] for k in commodities) <= arc_cap[arc]
        )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}