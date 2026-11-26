import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cap_1_2 = params["cap_1_2"]
    cap_1_3 = params["cap_1_3"]
    cap_2_3 = params["cap_2_3"]
    cap_2_4 = params["cap_2_4"]
    cap_3_4 = params["cap_3_4"]

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables for each directed edge
    f_1_2 = model.addVar(lb=0, ub=cap_1_2, name="f_1_2")
    f_1_3 = model.addVar(lb=0, ub=cap_1_3, name="f_1_3")
    f_2_3 = model.addVar(lb=0, ub=cap_2_3, name="f_2_3")
    f_2_4 = model.addVar(lb=0, ub=cap_2_4, name="f_2_4")
    f_3_4 = model.addVar(lb=0, ub=cap_3_4, name="f_3_4")

    # Maximize total flow into node 4
    model.setObjective(f_2_4 + f_3_4, GRB.MAXIMIZE)

    # Flow conservation at node 2: inflow = outflow
    model.addConstr(f_1_2 == f_2_3 + f_2_4, name="balance_node2")

    # Flow conservation at node 3: inflow = outflow
    model.addConstr(f_1_3 + f_2_3 == f_3_4, name="balance_node3")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}