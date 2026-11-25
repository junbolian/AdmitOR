import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 7
    nodes = list(range(n))

    # Build cost dict from params
    cost = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                key = f"cost_{i}_{j}"
                cost[(i, j)] = params[key]

    arcs = list(cost.keys())

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    ub = params["route_usage_upper_bound"]

    # Binary flow variables; ub must be 1 for BINARY — clamp to 1 if param says 1
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")
    # Respect route_usage_upper_bound: if 0, force all arcs off
    for arc in arcs:
        x[arc].UB = float(ub)

    # Objective: minimize total cost
    model.setObjective(gp.quicksum(cost[a] * x[a] for a in arcs), GRB.MINIMIZE)

    supply_0  = int(round(params["supply_node_0"]))
    demand_6  = int(round(params["demand_node_6"]))
    balance_mid = int(round(params["balance_nodes_1_to_5"]))

    # Flow balance constraints
    for nd in nodes:
        outflow = gp.quicksum(x[(nd, j)] for j in nodes if (nd, j) in arcs)
        inflow  = gp.quicksum(x[(i, nd)] for i in nodes if (i, nd) in arcs)

        if nd == 0:
            # net outflow = supply_node_0
            model.addConstr(outflow - inflow == supply_0, name=f"balance_{nd}")
        elif nd == 6:
            # net inflow = demand_node_6
            model.addConstr(inflow - outflow == demand_6, name=f"balance_{nd}")
        else:
            # intermediate: inflow - outflow = balance_mid (normally 0)
            model.addConstr(inflow - outflow == balance_mid, name=f"balance_{nd}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}