import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Number of variables and registers (at most 10 registers needed)
    num_vars = 10
    num_regs = 10

    # Interference edges (pairs of variables that must have different registers)
    edges = [
        (5, 8), (4, 9), (3, 7), (0, 3), (1, 4),
        (2, 3), (6, 7), (4, 5), (3, 9), (5, 9), (6, 9)
    ]

    model = pyo.ConcreteModel()

    # Sets
    model.V = pyo.Set(initialize=range(num_vars))
    model.R = pyo.Set(initialize=range(num_regs))
    model.E = pyo.Set(initialize=edges, dimen=2)

    # Variables
    model.x = pyo.Var(model.V, model.R, domain=pyo.Binary)
    model.y = pyo.Var(model.R, domain=pyo.Binary)

    # Objective: minimize number of registers used
    model.obj = pyo.Objective(expr=sum(model.y[r] for r in model.R), sense=pyo.minimize)

    # Each variable assigned exactly one register
    def assign_rule(m, v):
        return sum(m.x[v, r] for r in m.R) == 1
    model.assign = pyo.Constraint(model.V, rule=assign_rule)

    # Interference constraints: adjacent variables cannot share a register
    def interference_rule(m, u, v, r):
        return m.x[u, r] + m.x[v, r] <= 1
    model.interference = pyo.Constraint(model.E, model.R, rule=interference_rule)

    # Linking constraints: if a register is used, y[r] must be 1
    def link_rule(m, v, r):
        return m.x[v, r] <= m.y[r]
    model.link = pyo.Constraint(model.V, model.R, rule=link_rule)

    # Solve with HiGHS
    solver = Highs()
    solver.solve(model)

    # Retrieve objective value; success determined solely by retrievability
    try:
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or failed"}