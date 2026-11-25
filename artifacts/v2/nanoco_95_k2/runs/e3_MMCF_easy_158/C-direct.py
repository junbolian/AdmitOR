import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_nodes = params["num_nodes"]
    num_commodities = params["num_commodities"]
    arcs = params["arcs"]
    arc_capacity = params["arc_capacity"]
    arc_cost = params["arc_cost"]
    commodity_demand = params["commodity_demand"]
    commodity_source = params["commodity_source"]
    commodity_sink = params["commodity_sink"]

    num_arcs = len(arcs)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # flow[k][a] = flow of commodity k on arc a
    flow = {}
    for k in range(num_commodities):
        for a in range(num_arcs):
            flow[k, a] = model.addVar(lb=0.0, name=f"flow_{k}_{a}")

    # z = maximum utilization ratio across all arcs
    z = model.addVar(lb=0.0, name="z")

    model.setObjective(z, GRB.MINIMIZE)

    # Flow conservation constraints
    for k in range(num_commodities):
        src = commodity_source[k]
        snk = commodity_sink[k]
        dem = commodity_demand[k]
        for node in range(num_nodes):
            out_arcs = [a for a, (i, j) in enumerate(arcs) if i == node]
            in_arcs  = [a for a, (i, j) in enumerate(arcs) if j == node]
            if node == src:
                rhs = dem
            elif node == snk:
                rhs = -dem
            else:
                rhs = 0.0
            model.addConstr(
                gp.quicksum(flow[k, a] for a in out_arcs)
                - gp.quicksum(flow[k, a] for a in in_arcs)
                == rhs,
                name=f"flow_cons_k{k}_n{node}"
            )

    # Capacity and utilization constraints
    for a in range(num_arcs):
        cap = arc_capacity[a]
        total_flow = gp.quicksum(flow[k, a] for k in range(num_commodities))
        # Total flow <= capacity
        model.addConstr(total_flow <= cap, name=f"cap_{a}")
        # z >= utilization ratio for arc a
        model.addConstr(total_flow <= z * cap, name=f"util_{a}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}