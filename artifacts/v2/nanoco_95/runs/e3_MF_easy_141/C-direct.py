import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacities = params["capacities"]
    costs = params["costs"]

    # Routes in order: 0->1, 1->2, 1->7, 2->3, 2->6, 3->4, 3->8, 3->9,
    #                  4->5, 4->8, 5->6, 6->7, 7->8, 7->9, 8->9
    routes = [
        (0, 1), (1, 2), (1, 7), (2, 3), (2, 6), (3, 4), (3, 8), (3, 9),
        (4, 5), (4, 8), (5, 6), (6, 7), (7, 8), (7, 9), (8, 9)
    ]

    cap = {routes[i]: capacities[i] for i in range(15)}
    cst = {routes[i]: costs[i] for i in range(15)}

    # Outgoing and incoming route indices per node
    out_routes = {n: [r for r in routes if r[0] == n] for n in range(10)}
    in_routes  = {n: [r for r in routes if r[1] == n] for n in range(10)}

    # --- Phase 1: maximize flow ---
    model = gp.Model()
    model.setParam("OutputFlag", 0)

    flow = model.addVars(routes, lb=0.0, name="flow")
    total_flow = model.addVar(lb=0.0, name="total_flow")

    # Capacity constraints
    for r in routes:
        model.addConstr(flow[r] <= cap[r], name=f"cap_{r[0]}_{r[1]}")

    # Flow conservation at intermediate nodes 1-8
    for n in range(1, 9):
        model.addConstr(
            gp.quicksum(flow[r] for r in in_routes[n]) ==
            gp.quicksum(flow[r] for r in out_routes[n]),
            name=f"conserve_{n}"
        )

    # Source node 0: outflow = total_flow
    model.addConstr(
        gp.quicksum(flow[r] for r in out_routes[0]) == total_flow,
        name="source"
    )

    # Sink node 9: inflow = total_flow
    model.addConstr(
        gp.quicksum(flow[r] for r in in_routes[9]) == total_flow,
        name="sink"
    )

    model.setObjective(total_flow, GRB.MAXIMIZE)
    model.optimize()

    if model.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        return {"objective": None, "status": "infeasible_phase1"}

    max_flow_val = model.ObjVal

    # --- Phase 2: minimize cost subject to achieving max flow ---
    model2 = gp.Model()
    model2.setParam("OutputFlag", 0)

    flow2 = model2.addVars(routes, lb=0.0, name="flow2")

    # Capacity constraints
    for r in routes:
        model2.addConstr(flow2[r] <= cap[r], name=f"cap_{r[0]}_{r[1]}")

    # Flow conservation at intermediate nodes 1-8
    for n in range(1, 9):
        model2.addConstr(
            gp.quicksum(flow2[r] for r in in_routes[n]) ==
            gp.quicksum(flow2[r] for r in out_routes[n]),
            name=f"conserve_{n}"
        )

    # Fix total flow to the maximum found
    model2.addConstr(
        gp.quicksum(flow2[r] for r in out_routes[0]) == max_flow_val,
        name="source_fix"
    )
    model2.addConstr(
        gp.quicksum(flow2[r] for r in in_routes[9]) == max_flow_val,
        name="sink_fix"
    )

    model2.setObjective(
        gp.quicksum(cst[r] * flow2[r] for r in routes),
        GRB.MINIMIZE
    )
    model2.optimize()

    if model2.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        return {"objective": None, "status": "infeasible_phase2"}

    return {"objective": max_flow_val, "status": "optimal"}