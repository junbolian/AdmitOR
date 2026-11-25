import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacities = params["capacities"]
    costs = params["costs"]
    source_node = params["source_node"]
    sink_node = params["sink_node"]
    num_nodes = params["num_nodes"]
    num_arcs = params["num_arcs"]

    # Arc definitions (fixed structure)
    arcs = [
        (0,1),(1,2),(1,7),(2,3),(2,6),(3,4),(3,8),(3,9),
        (4,5),(4,8),(5,6),(6,7),(7,8),(7,9),(8,9)
    ]

    # Build adjacency structures
    out_arcs = {i: [] for i in range(num_nodes)}
    in_arcs  = {i: [] for i in range(num_nodes)}
    for idx, (u, v) in enumerate(arcs):
        out_arcs[u].append(idx)
        in_arcs[v].append(idx)

    model = gp.Model("emergency_relief")
    model.setParam("OutputFlag", 0)

    # Decision variables: flow on each arc
    flow = model.addVars(num_arcs, lb=0.0, name="flow")

    # Capacity constraints
    for idx in range(num_arcs):
        model.addConstr(flow[idx] <= capacities[idx], name=f"cap_{idx}")

    # Total flow variable (amount leaving source)
    total_flow = model.addVar(lb=0.0, name="total_flow")

    # Flow conservation
    for node in range(num_nodes):
        inflow  = gp.quicksum(flow[idx] for idx in in_arcs[node])
        outflow = gp.quicksum(flow[idx] for idx in out_arcs[node])
        if node == source_node:
            model.addConstr(outflow - inflow == total_flow, name=f"source_balance")
        elif node == sink_node:
            model.addConstr(inflow - outflow == total_flow, name=f"sink_balance")
        else:
            model.addConstr(inflow == outflow, name=f"balance_{node}")

    # Phase 1: maximize total flow
    model.setObjective(total_flow, GRB.MAXIMIZE)
    model.optimize()

    if model.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        return {"objective": None, "status": "infeasible_or_failed"}

    max_flow_val = total_flow.X

    # Phase 2: fix total flow and minimize cost
    model.addConstr(total_flow == max_flow_val, name="fix_flow")
    cost_obj = gp.quicksum(costs[idx] * flow[idx] for idx in range(num_arcs))
    model.setObjective(cost_obj, GRB.MINIMIZE)
    model.optimize()

    if model.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        return {"objective": None, "status": "cost_minimization_failed"}

    return {
        "objective": float(max_flow_val),
        "status": "optimal"
    }