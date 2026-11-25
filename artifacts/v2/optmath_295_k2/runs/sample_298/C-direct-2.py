import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply_node0 = params["supply_node0"]
    demand_node9 = params["demand_node9"]
    intermediate_net_flow = params["intermediate_net_flow"]

    # Ensure intermediate_net_flow is a scalar
    if hasattr(intermediate_net_flow, '__iter__'):
        intermediate_net_flow = float(list(intermediate_net_flow)[0])
    else:
        intermediate_net_flow = float(intermediate_net_flow)

    supply_node0 = float(supply_node0)
    demand_node9 = float(demand_node9)

    # Collect all arc costs from params
    arc_costs = {}
    for key, value in params.items():
        if key.startswith("cost_"):
            rest = key[len("cost_"):]
            parts = rest.split("_to_")
            if len(parts) == 2:
                src_str = parts[0]
                dst_str = parts[1]
                src_idx = int(src_str.replace("node", "").replace("_", ""))
                dst_idx = int(dst_str.replace("node", "").replace("_", ""))
                arc_costs[(src_idx, dst_idx)] = float(value)

    arcs = list(arc_costs.keys())

    model = gp.Model("min_cost_flow")
    model.setParam("OutputFlag", 0)

    x = {}
    for (i, j) in arcs:
        x[(i, j)] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.update()

    model.setObjective(
        gp.quicksum(arc_costs[(i, j)] * x[(i, j)] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Node 0: net outflow = supply_node0
    out0 = gp.quicksum(x[(i, j)] for (i, j) in arcs if i == 0)
    in0  = gp.quicksum(x[(i, j)] for (i, j) in arcs if j == 0)
    model.addConstr(out0 - in0 == supply_node0, name="supply_node0")

    # Node 9: net inflow = demand_node9
    out9 = gp.quicksum(x[(i, j)] for (i, j) in arcs if i == 9)
    in9  = gp.quicksum(x[(i, j)] for (i, j) in arcs if j == 9)
    model.addConstr(in9 - out9 == demand_node9, name="demand_node9")

    # Intermediate nodes 1..8: net flow = intermediate_net_flow
    for node in range(1, 9):
        out_n = gp.quicksum(x[(i, j)] for (i, j) in arcs if i == node)
        in_n  = gp.quicksum(x[(i, j)] for (i, j) in arcs if j == node)
        rhs = intermediate_net_flow
        model.addConstr(in_n - out_n == rhs, name=f"flow_node{node}")

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