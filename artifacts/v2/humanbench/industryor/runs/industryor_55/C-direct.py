import gurobipy as gp
from gurobipy import GRB


def solve(params):
    a = params["a"]
    b = params["b"]
    f = params["f"]
    q = params["q"]
    c_ik = params["c_ik"]
    c_kj = params["c_kj"]

    m = len(a)
    n = len(b)
    p = len(f)

    def get_cik(i, k):
        if isinstance(c_ik, dict):
            return c_ik[(i, k)]
        return c_ik[i][k]

    def get_ckj(k, j):
        if isinstance(c_kj, dict):
            return c_kj[(k, j)]
        return c_kj[k][j]

    model = gp.Model("fixed_charge_transshipment")
    model.Params.OutputFlag = 0

    x = model.addVars(m, p, lb=0, vtype=GRB.CONTINUOUS, name="x")
    y = model.addVars(p, n, lb=0, vtype=GRB.CONTINUOUS, name="y")
    z = model.addVars(p, vtype=GRB.BINARY, name="z")

    # Supply: shipments out of production point i cannot exceed a_i
    for i in range(m):
        model.addConstr(gp.quicksum(x[i, k] for k in range(p)) <= a[i])

    # Demand: exact requirement at each demand point j
    for j in range(n):
        model.addConstr(gp.quicksum(y[k, j] for k in range(p)) == b[j])

    # Flow conservation and capacity at transfer station k, linked to binary usage
    for k in range(p):
        model.addConstr(
            gp.quicksum(x[i, k] for i in range(m))
            == gp.quicksum(y[k, j] for j in range(n))
        )
        model.addConstr(gp.quicksum(x[i, k] for i in range(m)) <= q[k] * z[k])

    model.setObjective(
        gp.quicksum(f[k] * z[k] for k in range(p))
        + gp.quicksum(get_cik(i, k) * x[i, k] for i in range(m) for k in range(p))
        + gp.quicksum(get_ckj(k, j) * y[k, j] for k in range(p) for j in range(n)),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": "no_optimal_solution"}