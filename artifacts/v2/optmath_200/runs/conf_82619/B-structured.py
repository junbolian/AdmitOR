# IR: {"sets":{"N":[0,1,2,3],"A":"{(i,j) in N x N: i != j}"},"params":{"d[i,j]":"params['dij'] for each (i,j) in A"},"variables":{"x[i]":"binary, i in N","y[i,j]":"binary, (i,j) in A"},"constraints":["sum(x[i] for i in N) = 3","y[i,j] <= x[i] for (i,j) in A","y[i,j] <= x[j] for (i,j) in A","y[i,j] >= x[i] + x[j] - 1 for (i,j) in A"],"objective":"maximize sum(d[i,j] * y[i,j] for (i,j) in A); count both directions"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dispersion = {
        (0, 1): params["d01"],
        (0, 2): params["d02"],
        (0, 3): params["d03"],
        (1, 0): params["d10"],
        (1, 2): params["d12"],
        (1, 3): params["d13"],
        (2, 0): params["d20"],
        (2, 1): params["d21"],
        (2, 3): params["d23"],
        (3, 0): params["d30"],
        (3, 1): params["d31"],
        (3, 2): params["d32"],
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(4), ordered=True)
    model.arcs = pyo.Set(initialize=dispersion.keys(), dimen=2, ordered=True)
    model.dispersion = pyo.Param(
        model.arcs, initialize=dispersion, within=pyo.Reals
    )

    model.x = pyo.Var(model.nodes, domain=pyo.Binary)
    model.y = pyo.Var(model.arcs, domain=pyo.Binary)

    model.selection = pyo.Constraint(
        expr=sum(model.x[i] for i in model.nodes) == 3
    )
    model.activation_source = pyo.Constraint(
        model.arcs,
        rule=lambda mdl, i, j: mdl.y[i, j] <= mdl.x[i],
    )
    model.activation_destination = pyo.Constraint(
        model.arcs,
        rule=lambda mdl, i, j: mdl.y[i, j] <= mdl.x[j],
    )
    model.activation_lower = pyo.Constraint(
        model.arcs,
        rule=lambda mdl, i, j: mdl.y[i, j] >= mdl.x[i] + mdl.x[j] - 1,
    )

    model.total_dispersion = pyo.Objective(
        expr=sum(
            model.dispersion[i, j] * model.y[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_dispersion))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}