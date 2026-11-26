import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = {
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (1, 4): params["cost_1_4"],
        (1, 5): params["cost_1_5"],
        (2, 1): params["cost_2_1"],
        (2, 3): params["cost_2_3"],
        (2, 4): params["cost_2_4"],
        (2, 5): params["cost_2_5"],
        (3, 1): params["cost_3_1"],
        (3, 2): params["cost_3_2"],
        (3, 4): params["cost_3_4"],
        (3, 5): params["cost_3_5"],
        (4, 1): params["cost_4_1"],
        (4, 2): params["cost_4_2"],
        (4, 3): params["cost_4_3"],
        (4, 5): params["cost_4_5"],
        (5, 1): params["cost_5_1"],
        (5, 2): params["cost_5_2"],
        (5, 3): params["cost_5_3"],
        (5, 4): params["cost_5_4"],
    }

    supply = {
        1: params["supply_1"],
        2: params["supply_2"],
        3: params["supply_3"],
        4: params["supply_4"],
        5: params["supply_5"],
    }

    demand = {
        1: params["demand_1"],
        2: params["demand_2"],
        3: params["demand_3"],
        4: params["demand_4"],
        5: params["demand_5"],
    }

    regions = [1, 2, 3, 4, 5]
    arcs = list(cost.keys())

    model = gp.Model("railroad_relocation")
    model.setParam("OutputFlag", 0)

    # Decision variables: number of cars moved from region i to region j
    x = model.addVars(arcs, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Supply constraints: cars sent out from region i <= supply[i]
    for i in regions:
        outgoing = [(i, j) for (i, j) in arcs if i == i and (i, j) in cost]
        # net cars remaining in region i = supply[i] - sum of outgoing + sum of incoming >= demand[i]
        # Equivalently: sum_incoming - sum_outgoing >= demand[i] - supply[i]
        incoming_arcs = [(src, dst) for (src, dst) in arcs if dst == i]
        outgoing_arcs = [(src, dst) for (src, dst) in arcs if src == i]
        model.addConstr(
            supply[i]
            + gp.quicksum(x[src, dst] for (src, dst) in incoming_arcs)
            - gp.quicksum(x[src, dst] for (src, dst) in outgoing_arcs)
            >= demand[i],
            name=f"demand_{i}"
        )

    # Supply cap: cannot send out more cars than are available
    for i in regions:
        outgoing_arcs = [(src, dst) for (src, dst) in arcs if src == i]
        model.addConstr(
            gp.quicksum(x[src, dst] for (src, dst) in outgoing_arcs) <= supply[i],
            name=f"supply_{i}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}