import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Undirected edges and their param key suffixes
    edges = [
        (0, 1, "01_10"),
        (0, 5, "05_50"),
        (0, 7, "07_70"),
        (0, 8, "08_80"),
        (0, 9, "09_90"),
        (1, 2, "12_21"),
        (2, 3, "23_32"),
        (2, 9, "29_92"),
        (3, 4, "34_43"),
        (4, 5, "45_54"),
        (5, 6, "56_65"),
        (6, 7, "67_76"),
        (6, 9, "69_96"),
        (7, 8, "78_87"),
        (8, 9, "89_98"),
    ]

    # Build directed arc structures
    # arcs: list of (i, j)
    # capacity[(i,j)], cost[(i,j)]
    arcs = []
    capacity = {}
    cost = {}

    for u, v, suffix in edges:
        cap = params[f"arc_capacity_{suffix}"]
        uc = params[f"unit_cost_{suffix}"]
        arcs.append((u, v))
        arcs.append((v, u))
        capacity[(u, v)] = cap
        capacity[(v, u)] = cap
        cost[(u, v)] = uc
        cost[(v, u)] = uc

    # Flows: (flow_id, source, destination, demand)
    flows = [
        (1, 5, 4, params["demand_flow1_5_to_4"]),
        (2, 3, 0, params["demand_flow2_3_to_0"]),
    ]

    # Node set
    nodes = list(range(10))

    model = gp.Model("min_max_utilization")
    model.setParam("OutputFlag", 0)

    # Flow variables: x[k, i, j] = traffic of flow k on arc (i,j)
    x = {}
    for (k, s, d, dem) in flows:
        for (i, j) in arcs:
            x[k, i, j] = model.addVar(lb=0.0, name=f"x_{k}_{i}_{j}")

    # Max utilization variable
    u_max = model.addVar(lb=0.0, name="u_max")

    model.update()

    # Objective: minimize max utilization
    model.setObjective(u_max, GRB.MINIMIZE)

    # Flow conservation constraints
    for (k, s, d, dem) in flows:
        for nd in nodes:
            # outflow - inflow
            out_flow = gp.quicksum(x[k, nd, j] for (i, j) in arcs if i == nd)
            in_flow  = gp.quicksum(x[k, i, nd] for (i, j) in arcs if j == nd)
            if nd == s:
                model.addConstr(out_flow - in_flow == dem, name=f"flow_cons_{k}_{nd}")
            elif nd == d:
                model.addConstr(out_flow - in_flow == -dem, name=f"flow_cons_{k}_{nd}")
            else:
                model.addConstr(out_flow - in_flow == 0, name=f"flow_cons_{k}_{nd}")

    # Capacity constraints and utilization upper bound
    for (i, j) in arcs:
        cap = capacity[(i, j)]
        total_flow = gp.quicksum(x[k, i, j] for (k, s, d, dem) in flows)
        # Total flow <= capacity
        model.addConstr(total_flow <= cap, name=f"cap_{i}_{j}")
        # Utilization <= u_max  =>  total_flow / cap <= u_max
        model.addConstr(total_flow <= u_max * cap, name=f"util_{i}_{j}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}