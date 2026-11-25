import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    sizes = params["memory_sizes"]
    cap = params["block_capacity"]

    n = len(sizes)
    # At most n blocks are ever needed
    max_blocks = n

    model = pyo.ConcreteModel()

    model.OBJ = pyo.Set(initialize=range(n), ordered=True)
    model.BLK = pyo.Set(initialize=range(max_blocks), ordered=True)

    # x[i, b] = 1 if object i is placed into block b
    model.x = pyo.Var(model.OBJ, model.BLK, domain=pyo.Binary)
    # y[b] = 1 if block b is used (opened)
    model.y = pyo.Var(model.BLK, domain=pyo.Binary)

    # Each object assigned to exactly one block
    def assign_rule(m, i):
        return sum(m.x[i, b] for b in m.BLK) == 1

    model.assign_con = pyo.Constraint(model.OBJ, rule=assign_rule)

    # Capacity of each block must not be exceeded
    def cap_rule(m, b):
        return sum(sizes[i] * m.x[i, b] for i in m.OBJ) <= cap * m.y[b]

    model.cap_con = pyo.Constraint(model.BLK, rule=cap_rule)

    # Symmetry breaking: block b can only be used if block b-1 is used
    def sym_rule(m, b):
        if b == 0:
            return pyo.Constraint.Skip
        return m.y[b] <= m.y[b - 1]

    model.sym_con = pyo.Constraint(model.BLK, rule=sym_rule)

    # Objective: minimize number of used blocks
    model.total_blocks = pyo.Objective(
        expr=sum(model.y[b] for b in model.BLK), sense=pyo.minimize
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_blocks))
    return {"objective": obj_val, "status": "optimal"}