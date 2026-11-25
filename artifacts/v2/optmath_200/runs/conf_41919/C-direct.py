import gurobipy as gp
from gurobipy import GRB

def solve(params):
    P = 4
    C = 6

    def _get(val, k):
        if isinstance(val, dict):
            if k in val:
                return val[k]
            sk = str(k)
            if sk in val:
                return val[sk]
            raise KeyError(f"missing key {k!r}")
        return val[k]

    def _vector(name, length):
        return [_get(params[name], k) for k in range(length)]

    def _matrix(name):
        val = params[name]
        if isinstance(val, dict) and any(isinstance(k, tuple) for k in val.keys()):
            mat = []
            for i in range(P):
                row = []
                for j in range(C):
                    key = (i, j)
                    if key in val:
                        row.append(val[key])
                    elif str(key) in val:
                        row.append(val[str(key)])
                    else:
                        raise KeyError(f"missing cost key {key}")
                mat.append(row)
            return mat
        return [[_get(_get(val, i), j) for j in range(C)] for i in range(P)]

    capacity = [float(v) for v in _vector("capacity", P)]
    demand = [float(v) for v in _vector("demand", C)]
    min_producers = [float(v) for v in _vector("min_producers", C)]
    min_delivery = [float(v) for v in _vector("min_delivery", P)]
    cost = [[float(v) for v in row] for row in _matrix("cost")]

    model = gp.Model("energy_allocation")
    model.Params.OutputFlag = 0
    model.Params.MIPGap = 0.0

    x = model.addVars(P, C, lb=0.0, name="x")
    y = model.addVars(P, C, vtype=GRB.BINARY, name="y")

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(P) for j in range(C)),
        GRB.MINIMIZE,
    )

    for i in range(P):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(C)) <= capacity[i],
            name=f"capacity_{i}",
        )

    for j in range(C):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(P)) >= demand[j],
            name=f"demand_{j}",
        )
        model.addConstr(
            gp.quicksum(y[i, j] for i in range(P)) >= min_producers[j],
            name=f"min_producers_{j}",
        )

    for i in range(P):
        for j in range(C):
            model.addConstr(
                x[i, j] >= min_delivery[i] * y[i, j],
                name=f"min_delivery_{i}_{j}",
            )
            model.addConstr(
                x[i, j] <= capacity[i] * y[i, j],
                name=f"link_{i}_{j}",
            )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    return {"objective": None, "status": f"status_{model.status}"}