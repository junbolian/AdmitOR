import gurobipy as gp
from gurobipy import GRB

def solve(params):
    unit_cost = params["unit_cost"]
    min_flow  = params["min_flow"]
    capacity  = params["capacity"]

    # Pipe definitions (fixed topology)
    pipes = [
        (0,1),(0,2),(0,5),
        (1,0),(1,2),
        (2,0),(2,1),(2,3),
        (3,2),(3,4),
        (4,1),(4,2),(4,3),(4,5),
        (5,0),(5,3),(5,4),
    ]
    n_pipes = len(pipes)  # should equal params["num_pipes"]

    model = gp.Model("cooling_network")
    model.setParam("OutputFlag", 0)

    # Decision variables: flow on each pipe
    flow = {}
    for idx, (i, j) in enumerate(pipes):
        flow[(i,j)] = model.addVar(
            lb=min_flow[idx],
            ub=capacity[idx],
            name=f"f_{i}_{j}"
        )

    model.update()

    # Objective: minimize total pumping energy cost
    model.setObjective(
        gp.quicksum(unit_cost[idx] * flow[(i,j)] for idx, (i,j) in enumerate(pipes)),
        GRB.MINIMIZE
    )

    # Flow balance constraints: inflow == outflow at every node
    num_nodes = params["num_nodes"]
    for node in range(num_nodes):
        inflow  = gp.quicksum(flow[(i,j)] for (i,j) in pipes if j == node)
        outflow = gp.quicksum(flow[(i,j)] for (i,j) in pipes if i == node)
        model.addConstr(inflow == outflow, name=f"balance_{node}")

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