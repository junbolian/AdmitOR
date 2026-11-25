import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supply = [
        params["supply_node0"],
        params["supply_node1"],
        params["supply_node2"],
        params["supply_node3"],
        params["supply_node4"],
        params["supply_node5"],
    ]

    arcs = [
        (0, 2), (0, 3), (1, 2), (1, 3),
        (2, 4), (2, 5), (3, 4), (3, 5),
        (0, 4), (0, 5), (1, 4), (1, 5),
    ]

    capacity = {
        (0, 2): params["capacity_0_2"],
        (0, 3): params["capacity_0_3"],
        (1, 2): params["capacity_1_2"],
        (1, 3): params["capacity_1_3"],
        (2, 4): params["capacity_2_4"],
        (2, 5): params["capacity_2_5"],
        (3, 4): params["capacity_3_4"],
        (3, 5): params["capacity_3_5"],
        (0, 4): params["capacity_0_4"],
        (0, 5): params["capacity_0_5"],
        (1, 4): params["capacity_1_4"],
        (1, 5): params["capacity_1_5"],
    }

    cost = {
        (0, 2): params["cost_0_2"],
        (0, 3): params["cost_0_3"],
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (2, 4): params["cost_2_4"],
        (2, 5): params["cost_2_5"],
        (3, 4): params["cost_3_4"],
        (3, 5): params["cost_3_5"],
        (0, 4): params["cost_0_4"],
        (0, 5): params["cost_0_5"],
        (1, 4): params["cost_1_4"],
        (1, 5): params["cost_1_5"],
    }

    model = gp.Model("medical_supply_chain")
    model.setParam("OutputFlag", 0)

    flow = model.addVars(arcs, lb=0.0, name="flow")

    for (i, j) in arcs:
        model.addConstr(flow[i, j] <= capacity[i, j], name=f"cap_{i}_{j}")

    nodes = range(6)
    for node in nodes:
        outflow = gp.quicksum(flow[i, j] for (i, j) in arcs if i == node)
        inflow = gp.quicksum(flow[i, j] for (i, j) in arcs if j == node)
        model.addConstr(outflow - inflow == supply[node], name=f"balance_{node}")

    model.setObjective(
        gp.quicksum(cost[i, j] * flow[i, j] for (i, j) in arcs),
        GRB.MINIMIZE,
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