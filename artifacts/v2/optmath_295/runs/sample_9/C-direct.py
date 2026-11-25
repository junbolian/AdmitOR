import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply_node0 = params["supply_node0"]
    supply_node1 = params["supply_node1"]
    demand_node5 = params["demand_node5"]
    demand_node6 = params["demand_node6"]
    fixed_cost_matrix = params["fixed_cost_matrix"]
    variable_cost_matrix = params["variable_cost_matrix"]
    capacity_matrix = params["capacity_matrix"]

    # Directed edges in order given
    edges = [
        (0,1),(1,0),(0,2),(2,0),(0,3),(3,0),(0,4),(4,0),(0,5),(5,0),(0,6),(6,0),
        (1,2),(2,1),(1,3),(3,1),(1,4),(4,1),(1,5),(5,1),(1,6),(6,1),
        (2,3),(3,2),(2,4),(4,2),(2,5),(5,2),(2,6),(6,2),
        (3,4),(4,3),(3,5),(5,3),(3,6),(6,3),
        (4,5),(5,4),(4,6),(6,4),
        (5,6),(6,5)
    ]

    n_edges = len(edges)
    fixed_costs = {edges[k]: fixed_cost_matrix[k] for k in range(n_edges)}
    var_costs   = {edges[k]: variable_cost_matrix[k] for k in range(n_edges)}
    capacities  = {edges[k]: capacity_matrix[k] for k in range(n_edges)}

    # Net supply per node: positive = supply (outflow), negative = demand (inflow)
    # Nodes 2,3,4 are balanced (0)
    net_supply = {
        0:  supply_node0,
        1:  supply_node1,
        2:  0.0,
        3:  0.0,
        4:  0.0,
        5: -demand_node5,
        6: -demand_node6,
    }

    nodes = list(range(7))

    model = gp.Model("supply_chain")
    model.setParam("OutputFlag", 0)

    # Binary: establish connection
    y = model.addVars(edges, vtype=GRB.BINARY, name="y")
    # Continuous: flow on each arc
    x = model.addVars(edges, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    # Objective: fixed costs + variable costs
    model.setObjective(
        gp.quicksum(fixed_costs[e] * y[e] + var_costs[e] * x[e] for e in edges),
        GRB.MINIMIZE
    )

    # Flow balance: outflow - inflow = net_supply
    for node in nodes:
        outflow = gp.quicksum(x[(node, j)] for j in nodes if (node, j) in fixed_costs)
        inflow  = gp.quicksum(x[(i, node)] for i in nodes if (i, node) in fixed_costs)
        model.addConstr(outflow - inflow == net_supply[node], name=f"balance_{node}")

    # Capacity constraints: flow <= capacity * binary
    for e in edges:
        model.addConstr(x[e] <= capacities[e] * y[e], name=f"cap_{e[0]}_{e[1]}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}