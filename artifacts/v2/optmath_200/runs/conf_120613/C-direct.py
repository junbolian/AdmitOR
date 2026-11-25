import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Routes with transport costs per commodity
    # (i, j, commodity_index): cost
    transport_routes = {
        (0, 3, 1): params["transport_cost_c1_0_3"],
        (0, 1, 1): params["transport_cost_c1_0_1"],
        (0, 2, 1): params["transport_cost_c1_0_2"],
        (1, 2, 2): params["transport_cost_c2_1_2"],
        (1, 3, 2): params["transport_cost_c2_1_3"],
    }

    # Routes with facility installation
    facility_routes = {
        (0, 3): (params["install_cost_0_3"], params["capacity_0_3"]),
        (1, 2): (params["install_cost_1_2"], params["capacity_1_2"]),
        (1, 3): (params["install_cost_1_3"], params["capacity_1_3"]),
        (2, 0): (params["install_cost_2_0"], params["capacity_2_0"]),
        (2, 1): (params["install_cost_2_1"], params["capacity_2_1"]),
        (3, 1): (params["install_cost_3_1"], params["capacity_3_1"]),
        (3, 2): (params["install_cost_3_2"], params["capacity_3_2"]),
    }

    # Commodity definitions: (origin, destination)
    commodities = {1: (0, 3), 2: (1, 2)}

    # All arcs per commodity (from transport_routes)
    arcs_per_commodity = {k: [] for k in commodities}
    for (i, j, k) in transport_routes:
        arcs_per_commodity[k].append((i, j))

    # All nodes
    nodes = set(range(4))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Flow variables: f[i,j,k] in [0,1]
    flow = {}
    for (i, j, k), cost in transport_routes.items():
        flow[(i, j, k)] = model.addVar(lb=0.0, ub=1.0, vtype=GRB.CONTINUOUS,
                                        name=f"flow_{i}_{j}_{k}")

    # Facility variables: y[i,j] >= 0 integer
    facility = {}
    for (i, j) in facility_routes:
        facility[(i, j)] = model.addVar(lb=0, vtype=GRB.INTEGER,
                                         name=f"facility_{i}_{j}")

    # Objective: minimize transport costs + installation costs
    obj = gp.LinExpr()
    for (i, j, k), cost in transport_routes.items():
        obj += cost * flow[(i, j, k)]
    for (i, j), (inst_cost, cap) in facility_routes.items():
        obj += inst_cost * facility[(i, j)]
    model.setObjective(obj, GRB.MINIMIZE)

    # Flow conservation constraints
    # For each commodity k with origin o and destination d:
    #   sum of flow out of node n - sum of flow into node n = supply[n]
    #   supply[o] = 1, supply[d] = -1, supply[others] = 0
    for k, (origin, dest) in commodities.items():
        for node in nodes:
            out_flow = gp.LinExpr()
            in_flow = gp.LinExpr()
            for (i, j, kk) in transport_routes:
                if kk != k:
                    continue
                if i == node:
                    out_flow += flow[(i, j, k)]
                if j == node:
                    in_flow += flow[(i, j, k)]
            if node == origin:
                supply = 1.0
            elif node == dest:
                supply = -1.0
            else:
                supply = 0.0
            # Only add constraint if node appears in any arc for this commodity
            # (avoids trivial 0=0 constraints, but harmless to include)
            model.addConstr(out_flow - in_flow == supply,
                            name=f"flow_conservation_k{k}_n{node}")

    # Capacity constraints: total flow on route (i,j) <= capacity * facilities installed
    # Group flow variables by arc (i,j) across all commodities
    arc_flows = {}
    for (i, j, k) in transport_routes:
        arc = (i, j)
        if arc not in arc_flows:
            arc_flows[arc] = gp.LinExpr()
        arc_flows[arc] += flow[(i, j, k)]

    for (i, j), (inst_cost, cap) in facility_routes.items():
        total_flow = arc_flows.get((i, j), gp.LinExpr())
        model.addConstr(total_flow <= cap * facility[(i, j)],
                        name=f"capacity_{i}_{j}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}