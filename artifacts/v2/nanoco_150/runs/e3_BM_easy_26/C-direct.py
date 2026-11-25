import gurobipy as gp
from gurobipy import GRB

def solve(params):
    links = [
        (0, 3), (0, 4), (1, 8), (2, 3), (2, 6), (2, 7),
        (3, 6), (3, 7), (3, 8), (3, 9), (4, 5), (4, 6),
        (4, 7), (4, 8), (4, 9), (5, 7), (6, 7)
    ]

    revenue = {
        (0, 3): params["revenue_0_3"],
        (0, 4): params["revenue_0_4"],
        (1, 8): params["revenue_1_8"],
        (2, 3): params["revenue_2_3"],
        (2, 6): params["revenue_2_6"],
        (2, 7): params["revenue_2_7"],
        (3, 6): params["revenue_3_6"],
        (3, 7): params["revenue_3_7"],
        (3, 8): params["revenue_3_8"],
        (3, 9): params["revenue_3_9"],
        (4, 5): params["revenue_4_5"],
        (4, 6): params["revenue_4_6"],
        (4, 7): params["revenue_4_7"],
        (4, 8): params["revenue_4_8"],
        (4, 9): params["revenue_4_9"],
        (5, 7): params["revenue_5_7"],
        (6, 7): params["revenue_6_7"],
    }

    capacity = {
        0: params["capacity_0"],
        1: params["capacity_1"],
        2: params["capacity_2"],
        3: params["capacity_3"],
        4: params["capacity_4"],
        5: params["capacity_5"],
        6: params["capacity_6"],
        7: params["capacity_7"],
        8: params["capacity_8"],
        9: params["capacity_9"],
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(links, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(revenue[lnk] * x[lnk] for lnk in links),
        GRB.MAXIMIZE
    )

    stations = range(10)
    for s in stations:
        incident = [lnk for lnk in links if s in lnk]
        if incident:
            model.addConstr(
                gp.quicksum(x[lnk] for lnk in incident) <= capacity[s],
                name=f"cap_{s}"
            )

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