import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand_0 = params["demand_0"]
    demand_1 = params["demand_1"]
    supply_4 = params["supply_4"]
    supply_5 = params["supply_5"]

    # Fixed costs (row=from, col=to), diagonal unused
    fixed_cost = [
        [0,    1955, 2050, 1953, 1952, 2046],
        [2009, 0,    1994, 1999, 2023, 2042],
        [1973, 2020, 0,    1990, 2011, 2008],
        [2026, 1991, 2006, 0,    1979, 1967],
        [2046, 2041, 2002, 2030, 0,    2015],
        [2020, 1973, 2022, 1966, 1951, 0   ],
    ]

    # Variable costs per unit (row=from, col=to)
    variable_cost = [
        [0,  20, 20, 19, 21, 20],
        [21,  0, 19, 21, 19, 20],
        [21, 21,  0, 20, 19, 19],
        [20, 20, 19,  0, 20, 19],
        [19, 19, 21, 20,  0, 21],
        [21, 19, 19, 20, 20,  0],
    ]

    # Capacities (row=from, col=to)
    capacity = [
        [0,   129, 131, 246, 208, 152],
        [149,   0, 147, 164, 135, 229],
        [250, 131,   0, 177, 144, 170],
        [163, 196, 228,   0, 150, 185],
        [225, 205, 215, 240,   0, 243],
        [154, 230, 182, 248, 146,   0],
    ]

    n = 6
    nodes = range(n)
    # positive = supply, negative = demand
    net_supply = [-demand_0, -demand_1, 0.0, 0.0, supply_4, supply_5]

    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = gp.Model("supply_chain")
    model.setParam("OutputFlag", 0)

    flow = model.addVars(arcs, lb=0.0, name="flow")
    active = model.addVars(arcs, vtype=GRB.BINARY, name="active")

    model.setObjective(
        gp.quicksum(
            fixed_cost[i][j] * active[i, j] + variable_cost[i][j] * flow[i, j]
            for i, j in arcs
        ),
        GRB.MINIMIZE,
    )

    for i, j in arcs:
        model.addConstr(flow[i, j] <= capacity[i][j] * active[i, j], name=f"cap_{i}_{j}")

    for k in nodes:
        inflow = gp.quicksum(flow[i, k] for i in nodes if i != k)
        outflow = gp.quicksum(flow[k, j] for j in nodes if j != k)
        model.addConstr(outflow - inflow == net_supply[k], name=f"balance_{k}")

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