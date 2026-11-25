import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Structural data: feasible task-server compatibility paths
    edges = [
        (0, 3), (0, 4),
        (1, 0), (1, 3), (1, 4),
        (2, 0), (2, 3),
        (3, 1), (3, 2),
        (4, 0), (4, 1),
        (5, 2),
        (6, 0), (6, 3), (6, 4),
    ]

    tasks = list(range(7))
    servers = list(range(5))

    model = pyo.ConcreteModel()

    model.task_idx = pyo.Set(initialize=tasks)
    model.server_idx = pyo.Set(initialize=servers)
    model.edge_idx = pyo.Set(initialize=list(range(len(edges))))

    # edge_task[k] = task of edge k, edge_server[k] = server of edge k
    model.edge_task = pyo.Param(
        model.edge_idx, initialize={k: e[0] for k, e in enumerate(edges)}, within=pyo.Any
    )
    model.edge_server = pyo.Param(
        model.edge_idx, initialize={k: e[1] for k, e in enumerate(edges)}, within=pyo.Any
    )

    model.routes = pyo.Var(model.edge_idx, domain=pyo.Binary)

    # Each task assigned to at most one server
    model.task_limit = pyo.Constraint(
        model.task_idx,
        rule=lambda m, t: sum(
            m.routes[k] for k in m.edge_idx if m.edge_task[k] == t
        ) <= 1,
    )

    # Each server receives at most one task
    model.server_limit = pyo.Constraint(
        model.server_idx,
        rule=lambda m, s: sum(
            m.routes[k] for k in m.edge_idx if m.edge_server[k] == s
        ) <= 1,
    )

    model.obj = pyo.Objective(
        expr=sum(model.routes[k] for k in model.edge_idx),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}