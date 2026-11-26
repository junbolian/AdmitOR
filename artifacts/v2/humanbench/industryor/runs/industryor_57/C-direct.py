import gurobipy as gp
from gurobipy import GRB

def solve(params):
    area_per_store = params["area_per_store"]   # list of 5 values, index 0..4
    min_stores     = params["min_stores"]        # list of 5 values
    max_stores     = params["max_stores"]        # list of 3 values (for types 1..3, i.e. index 0,1,2)
    profit_type1   = params["profit_type1"]      # list of 3: per-store profits at n=1,2,3
    profit_type2   = params["profit_type2"]      # list of 2: per-store profits at n=1,2
    profit_type3   = params["profit_type3"]      # list of 3: per-store profits at n=1,2,3
    profit_type4   = params["profit_type4"]      # list of 2: per-store profits at n=1,2
    profit_type5   = params["profit_type5"]      # list of 3: per-store profits at n=1,2,3
    rent_share     = params["rent_share"]        # fraction, e.g. 0.20

    profits_per_store = [
        profit_type1,   # type 0 (Jewelry):         n=1,2,3
        profit_type2,   # type 1 (Shoes and Hats):  n=1,2
        profit_type3,   # type 2 (Department Store): n=1,2,3
        profit_type4,   # type 3 (Bookstore):        n=1,2
        profit_type5,   # type 4 (Restaurant):       n=1,2,3
    ]

    # min for all 5 types
    type_min = [int(min_stores[i]) for i in range(5)]

    # max: params provides max_stores for types 0,1,2 (3 entries);
    # for types 3 and 4, infer max from length of their profit lists
    type_max = []
    for i in range(3):
        type_max.append(int(max_stores[i]))
    for i in range(3, 5):
        type_max.append(len(profits_per_store[i]))

    total_area = 5000

    model = gp.Model("mall_rental")
    model.setParam("OutputFlag", 0)

    # Binary variable z[i, n] = 1 if exactly n stores of type i are opened
    z = {}
    for i in range(5):
        lo = type_min[i]
        hi = type_max[i]
        for n in range(lo, hi + 1):
            z[i, n] = model.addVar(vtype=GRB.BINARY, name=f"z_{i}_{n}")

    model.update()

    # Exactly one count selected per type
    for i in range(5):
        lo = type_min[i]
        hi = type_max[i]
        model.addConstr(
            gp.quicksum(z[i, n] for n in range(lo, hi + 1)) == 1,
            name=f"one_count_{i}"
        )

    # Total area constraint
    area_expr = gp.LinExpr()
    for i in range(5):
        lo = type_min[i]
        hi = type_max[i]
        for n in range(lo, hi + 1):
            area_expr += area_per_store[i] * n * z[i, n]
    model.addConstr(area_expr <= total_area, name="area_limit")

    # Objective: maximize rent = rent_share * sum_i [ n_i * per_store_profit_i(n_i) ]
    obj = gp.LinExpr()
    for i in range(5):
        lo = type_min[i]
        hi = type_max[i]
        for n in range(lo, hi + 1):
            if n == 0:
                total_profit_n = 0.0
            else:
                per_store = profits_per_store[i][n - 1]
                total_profit_n = n * per_store
            obj += rent_share * total_profit_n * z[i, n]

    model.setObjective(obj, GRB.MAXIMIZE)
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