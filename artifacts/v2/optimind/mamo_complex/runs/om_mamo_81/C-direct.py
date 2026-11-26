def solve(params):
    import gurobipy as gp
    from gurobipy import GRB

    # Build edge list and weights from params
    edges = {
        ('S', '2'): params["w_S_2"],
        ('S', '3'): params["w_S_3"],
        ('2', 'S'): params["w_2_S"],
        ('2', '4'): params["w_2_4"],
        ('2', '3'): params["w_2_3"],
        ('3', 'S'): params["w_3_S"],
        ('3', '2'): params["w_3_2"],
        ('3', '5'): params["w_3_5"],
        ('3', '6'): params["w_3_6"],
        ('4', '2'): params["w_4_2"],
        ('4', '6'): params["w_4_6"],
        ('5', '3'): params["w_5_3"],
        ('5', 'T'): params["w_5_T"],
        ('6', '3'): params["w_6_3"],
        ('6', '4'): params["w_6_4"],
        ('6', '7'): params["w_6_7"],
        ('7', '6'): params["w_7_6"],
        ('7', 'T'): params["w_7_T"],
        ('T', '5'): params["w_T_5"],
        ('T', '7'): params["w_T_7"],
    }

    nodes = ['S', '2', '3', '4', '5', '6', '7', 'T']
    source = 'S'
    sink = 'T'

    model = gp.Model("shortest_path")
    model.setParam("OutputFlag", 0)

    # Binary variable for each edge: 1 if edge is on the path
    x = model.addVars(edges.keys(), vtype=GRB.BINARY, name="x")

    # Objective: minimize total edge weight
    model.setObjective(
        gp.quicksum(edges[e] * x[e] for e in edges.keys()),
        GRB.MINIMIZE
    )

    # Flow conservation constraints
    for node in nodes:
        outflow = gp.quicksum(x[e] for e in edges.keys() if e[0] == node)
        inflow  = gp.quicksum(x[e] for e in edges.keys() if e[1] == node)

        if node == source:
            model.addConstr(outflow - inflow == 1, name=f"flow_{node}")
        elif node == sink:
            model.addConstr(outflow - inflow == -1, name=f"flow_{node}")
        else:
            model.addConstr(outflow - inflow == 0, name=f"flow_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}