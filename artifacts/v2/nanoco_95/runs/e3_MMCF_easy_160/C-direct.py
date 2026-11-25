import gurobipy as gp
from gurobipy import GRB

def solve(params):
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]
    commodity_supplies = params["commodity_supplies"]
    node_coordinates_x = params["node_coordinates_x"]
    node_coordinates_y = params["node_coordinates_y"]

    num_nodes = 9
    num_commodities = 2

    arcs = [
        (0,1),(1,0),(0,3),(3,0),(0,5),(5,0),
        (1,2),(2,1),(1,7),(7,1),
        (2,3),(3,2),(2,6),(6,2),(2,7),(7,2),
        (3,4),(4,3),(4,5),(5,4),(4,6),(6,4),
        (5,6),(6,5),(6,7),(7,6),(7,8),(8,7)
    ]

    # Commodity definitions: (source, sink, supply)
    commodities = [
        (3, 2, commodity_supplies[0]),
        (6, 1, commodity_supplies[1]),
    ]

    cap = {arcs[i]: arc_capacities[i] for i in range(len(arcs))}

    model = gp.Model("cold_chain_minmax_util")
    model.setParam("OutputFlag", 0)

    # Flow variables: flow[k][arc]
    flow = {}
    for k in range(num_commodities):
        flow[k] = {}
        for arc in arcs:
            flow[k][arc] = model.addVar(lb=0.0, name=f"flow_{k}_{arc[0]}_{arc[1]}")

    # Max utilization variable
    z = model.addVar(lb=0.0, name="z")

    model.setObjective(z, GRB.MINIMIZE)

    # Flow conservation constraints
    for k in range(num_commodities):
        src, snk, supply = commodities[k]
        for nd in range(num_nodes):
            out_flow = gp.quicksum(flow[k][arc] for arc in arcs if arc[0] == nd)
            in_flow  = gp.quicksum(flow[k][arc] for arc in arcs if arc[1] == nd)
            if nd == src:
                model.addConstr(out_flow - in_flow == supply, name=f"cons_{k}_{nd}")
            elif nd == snk:
                model.addConstr(in_flow - out_flow == supply, name=f"cons_{k}_{nd}")
            else:
                model.addConstr(out_flow - in_flow == 0, name=f"cons_{k}_{nd}")

    # Capacity constraints and utilization bound
    for arc in arcs:
        cap_val = cap[arc]
        total = gp.quicksum(flow[k][arc] for k in range(num_commodities))
        model.addConstr(total <= cap_val, name=f"cap_{arc[0]}_{arc[1]}")
        model.addConstr(total <= z * cap_val, name=f"util_{arc[0]}_{arc[1]}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}