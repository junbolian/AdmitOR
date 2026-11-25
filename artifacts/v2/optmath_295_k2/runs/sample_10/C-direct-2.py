import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n_nodes = 7
    nodes = list(range(n_nodes))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    cost = {}
    for (i, j) in arcs:
        key = f"arc_cost_{i}_{j}"
        cost[(i, j)] = params[key]

    supply_0 = params["supply_node_0"]
    demand_6 = params["demand_node_6"]
    balance_mid = params["balance_nodes_1_5"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[(i, j)] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # node_0: outflow - inflow = supply_0
    model.addConstr(
        gp.quicksum(x[(0, j)] for j in nodes if j != 0)
        - gp.quicksum(x[(i, 0)] for i in nodes if i != 0)
        == supply_0,
        name="supply_node0"
    )

    # node_6: inflow - outflow = demand_6
    model.addConstr(
        gp.quicksum(x[(i, 6)] for i in nodes if i != 6)
        - gp.quicksum(x[(6, j)] for j in nodes if j != 6)
        == demand_6,
        name="demand_node6"
    )

    # intermediate nodes 1..5: flow balance = balance_mid (expected 0)
    for nd in range(1, 6):
        model.addConstr(
            gp.quicksum(x[(i, nd)] for i in nodes if i != nd)
            - gp.quicksum(x[(nd, j)] for j in nodes if j != nd)
            == balance_mid,
            name=f"balance_node{nd}"
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
        return {"objective": None, "status": f"solver_status_{status}"}