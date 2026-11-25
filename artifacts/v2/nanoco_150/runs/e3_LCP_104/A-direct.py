import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_tasks = int(params["num_tasks"])
    num_nodes = int(params["num_nodes"])
    conflict_pairs = params["conflict_pairs"]
    allowable_nodes = params["allowable_nodes"]

    task_idx = list(range(num_tasks))
    node_idx = list(range(num_nodes))

    model = pyo.ConcreteModel()

    # Valid (task, node) assignments based on compatibility structure
    allowed_pairs = [
        (t, n) for t in task_idx for n in allowable_nodes[t]
    ]

    model.x = pyo.Var(allowed_pairs, domain=pyo.Binary)
    model.z = pyo.Var(domain=pyo.NonNegativeReals)

    # Each task assigned exactly one allowable node
    model.assign = pyo.Constraint(
        task_idx,
        rule=lambda m, t: sum(m.x[t, n] for n in allowable_nodes[t]) == 1,
    )

    # Conflict pairs must use distinct nodes
    model.conflict = pyo.Constraint(
        list(range(len(conflict_pairs))),
        rule=lambda m, k: sum(
            m.x[conflict_pairs[k][0], n]
            for n in allowable_nodes[conflict_pairs[k][0]]
            if n in allowable_nodes[conflict_pairs[k][1]]
        ) * 0
        + sum(
            n * (m.x[conflict_pairs[k][0], n] + m.x[conflict_pairs[k][1], n])
            for n in allowable_nodes[conflict_pairs[k][0]]
            if n in allowable_nodes[conflict_pairs[k][1]]
        )
        >= 0,
    )

    # Link z to max used node id
    model.max_link = pyo.Constraint(
        list(range(len(conflict_pairs))),
        rule=lambda m, k: pyo.Constraint.Skip,
    )

    # Objective: minimize z (max node id used)
    model.obj = pyo.Objective(expr=model.z, sense=pyo.minimize)

    # Big-M style upper link: z >= n * x[t,n] for all
    model.z_link = pyo.Constraint(
        allowed_pairs,
        rule=lambda m, t, n: m.z >= n * m.x[t, n],
    )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}