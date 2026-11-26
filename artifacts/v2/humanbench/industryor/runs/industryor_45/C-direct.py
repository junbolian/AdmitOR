import gurobipy as gp
from gurobipy import GRB

def solve(params):
    m_mass = params["m"]
    H = params["H"]
    T = params["T"]
    b = params["b"]
    g = params["g"]
    n = int(params["n"])

    dt = T / n  # time step size

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: thrust at each time step k = 0, 1, ..., n
    # Allow thrust in range [0, b]
    u = model.addVars(n + 1, lb=0.0, ub=b, name="u")

    # State variables: velocity v[k] and position y[k] at each step k = 0, ..., n
    v = model.addVars(n + 1, lb=-GRB.INFINITY, name="v")
    y = model.addVars(n + 1, lb=-GRB.INFINITY, name="y")

    # Initial conditions
    model.addConstr(y[0] == 0.0, name="init_y")
    model.addConstr(v[0] == 0.0, name="init_v")

    # Dynamics via trapezoidal discretization:
    # a[k] = u[k]/m_mass - g
    # v[k+1] = v[k] + dt/2 * (a[k] + a[k+1])
    # y[k+1] = y[k] + dt/2 * (v[k] + v[k+1])
    for k in range(n):
        model.addConstr(
            v[k + 1] == v[k] + (dt / 2.0) * ((u[k] / m_mass - g) + (u[k + 1] / m_mass - g)),
            name=f"vel_{k}"
        )
        model.addConstr(
            y[k + 1] == y[k] + (dt / 2.0) * (v[k] + v[k + 1]),
            name=f"pos_{k}"
        )

    # Must reach height H by time T
    model.addConstr(y[n] >= H, name="height_req")

    # Objective: minimize total energy consumption (sum of thrust forces over time)
    model.setObjective(
        gp.quicksum(u[k] * dt for k in range(n + 1)),
        GRB.MINIMIZE
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
        return {"objective": None, "status": f"status_{status}"}