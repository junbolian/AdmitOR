import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_nodes = params["num_nodes"]
    num_arcs = params["num_arcs"]
    num_commodities = params["num_commodities"]
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]
    commodity_supply = params["commodity_supply"]
    commodity_source = params["commodity_source"]
    commodity_sink = params["commodity_sink"]

    # Directed arcs in fixed order
    arcs = [
        (0,1),(1,0),(0,3),(3,0),(0,5),(5,0),
        (1,2),(2,1),(1,7),(7,1),
        (2,3),(3,2),(2,6),(6,2),(2,7),(7,2),
        (3,4),(4,3),(4,5),(5,4),(4,6),(6,4),
        (5,6),(6,5),(6,7),(7,6),(7,8),(8,7)
    ]

    arc_index = {a: i for i, a in enumerate(arcs)}

    # Build adjacency structures
    out_arcs = {v: [] for v in range(num_nodes)}
    in_arcs  = {v: [] for v in range(num_nodes)}
    for (u, v) in arcs:
        out_arcs[u].append((u, v))
        in_arcs[v].append((u, v))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Flow variables: f[k][arc]
    f = {}
    for k in range(num_commodities):
        for arc in arcs:
            f[k, arc] = model.addVar(lb=0.0, name=f"f_{k}_{arc[0]}_{arc[1]}")

    # Auxiliary variable: maximum utilization rate
    z = model.addVar(lb=0.0, name="z")

    model.setObjective(z, GRB.MINIMIZE)

    # Flow conservation constraints
    for k in range(num_commodities):
        src = commodity_source[k]
        snk = commodity_sink[k]
        supply = commodity_supply[k]
        for v in range(num_nodes):
            if v == src:
                rhs = supply
            elif v == snk:
                rhs = -supply
            else:
                rhs = 0.0
            model.addConstr(
                gp.quicksum(f[k, a] for a in out_arcs[v]) -
                gp.quicksum(f[k, a] for a in in_arcs[v]) == rhs,
                name=f"flow_cons_k{k}_v{v}"
            )

    # Capacity and utilization constraints
    for arc in arcs:
        idx = arc_index[arc]
        cap = arc_capacities[idx]
        total_flow = gp.quicksum(f[k, arc] for k in range(num_commodities))
        # Aggregate capacity
        model.addConstr(total_flow <= cap, name=f"cap_{arc[0]}_{arc[1]}")
        # z >= utilization rate on this arc
        model.addConstr(total_flow <= z * cap, name=f"util_{arc[0]}_{arc[1]}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}