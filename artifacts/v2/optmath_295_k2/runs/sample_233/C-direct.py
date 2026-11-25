import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]                    # 2D list or dict indexed by (producer, contract)
    capacity = params["capacity"]            # list or dict indexed by producer
    demand = params["demand"]                # list or dict indexed by contract
    min_producers = params["min_producers"]  # list or dict indexed by contract
    min_delivery = params["min_delivery"]    # list or dict indexed by producer

    # Normalize to lists if needed
    if hasattr(capacity, 'keys'):
        producers = list(capacity.keys())
        cap = {p: capacity[p] for p in producers}
    else:
        producers = list(range(len(capacity)))
        cap = {p: capacity[p] for p in producers}

    if hasattr(demand, 'keys'):
        contracts = list(demand.keys())
        dem = {c: demand[c] for c in contracts}
    else:
        contracts = list(range(len(demand)))
        dem = {c: demand[c] for c in contracts}

    if hasattr(min_producers, 'keys'):
        min_prod = {c: min_producers[c] for c in contracts}
    else:
        min_prod = {c: min_producers[c] for c in contracts}

    if hasattr(min_delivery, 'keys'):
        min_del = {p: min_delivery[p] for p in producers}
    else:
        min_del = {p: min_delivery[p] for p in producers}

    # Normalize cost to dict keyed by (producer, contract)
    if hasattr(cost, 'keys'):
        cst = {(p, c): cost[(p, c)] for p in producers for c in contracts}
    else:
        # cost is a 2D list: cost[producer][contract]
        cst = {(p, c): cost[p][c] for p in producers for c in contracts}

    model = gp.Model("electricity_scheduling")
    model.Params.OutputFlag = 0

    # Delivery quantities: x[p, c] >= 0
    x = model.addVars(producers, contracts, lb=0.0, vtype=GRB.CONTINUOUS, name="x")
    # Assignment binaries: y[p, c] = 1 if producer p serves contract c
    y = model.addVars(producers, contracts, vtype=GRB.BINARY, name="y")

    # Objective: minimize total production cost
    model.setObjective(
        gp.quicksum(cst[(p, c)] * x[p, c] for p in producers for c in contracts),
        GRB.MINIMIZE,
    )

    # Capacity per producer
    for p in producers:
        model.addConstr(
            gp.quicksum(x[p, c] for c in contracts) <= cap[p],
            name=f"capacity_{p}",
        )

    # Demand per contract
    for c in contracts:
        model.addConstr(
            gp.quicksum(x[p, c] for p in producers) >= dem[c],
            name=f"demand_{c}",
        )

    # Minimum number of contributing producers per contract
    for c in contracts:
        model.addConstr(
            gp.quicksum(y[p, c] for p in producers) >= min_prod[c],
            name=f"minproducers_{c}",
        )

    # Big-M: each producer's total capacity is a valid upper bound per contract
    for p in producers:
        for c in contracts:
            model.addConstr(
                x[p, c] >= min_del[p] * y[p, c],
                name=f"minlink_{p}_{c}",
            )
            model.addConstr(
                x[p, c] <= cap[p] * y[p, c],
                name=f"maxlink_{p}_{c}",
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.Status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    if model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    return {"objective": None, "status": f"failed_status_{model.Status}"}