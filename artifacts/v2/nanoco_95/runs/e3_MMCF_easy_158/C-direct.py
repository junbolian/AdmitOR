import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacities = params["capacities"]
    costs = params["costs"]
    demands = params["demands"]
    num_nodes = params["num_nodes"]
    num_commodities = params["num_commodities"]

    arcs = [
        (0,1),(1,0),(0,3),(3,0),(0,5),(5,0),(0,6),(6,0),(0,7),(7,0),
        (1,2),(2,1),(1,5),(5,1),(1,6),(6,1),(2,3),(3,2),(2,6),(6,2),
        (3,4),(4,3),(4,5),(5,4),(4,6),(6,4),(4,7),(7,4),(5,6),(6,5),
        (5,7),(7,5),(6,7),(7,6)
    ]
    num_arcs = len(arcs)

    # Commodity definitions: (source, sink, demand)
    # commodity 0: 3->7, demand = demands[0]
    # commodity 1: 1->5, demand = demands[1]
    commodities = [
        (3, 7, demands[0]),
        (1, 5, demands[1]),
    ]

    arc_index = {arc: i for i, arc in enumerate(arcs)}

    model = gp.Model("multiproduct_pipeline")
    model.setParam("OutputFlag", 0)

    # Flow variables: f[k][a] = flow of commodity k on arc a
    f = {}
    for k in range(num_commodities):
        for a in range(num_arcs):
            f[k, a] = model.addVar(lb=0.0, name=f"f_{k}_{a}")

    # Minimax utilization variable
    z = model.addVar(lb=0.0, name="z")

    model.setObjective(z, GRB.MINIMIZE)

    # Flow conservation constraints
    nodes = list(range(num_nodes))
    for k in range(num_commodities):
        src, snk, demand = commodities[k]
        for node in nodes:
            # outflow - inflow
            out_arcs = [arc_index[(node, j)] for (i, j) in arcs if i == node]
            in_arcs  = [arc_index[(i, node)] for (i, j) in arcs if j == node]
            lhs = (
                gp.quicksum(f[k, a] for a in out_arcs)
                - gp.quicksum(f[k, a] for a in in_arcs)
            )
            if node == src:
                rhs = demand
            elif node == snk:
                rhs = -demand
            else:
                rhs = 0.0
            model.addConstr(lhs == rhs, name=f"flow_cons_k{k}_n{node}")

    # Capacity and utilization constraints
    for a in range(num_arcs):
        cap = capacities[a]
        total_flow = gp.quicksum(f[k, a] for k in range(num_commodities))
        # Capacity constraint
        model.addConstr(total_flow <= cap, name=f"cap_{a}")
        # Utilization <= z  =>  total_flow / cap <= z
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