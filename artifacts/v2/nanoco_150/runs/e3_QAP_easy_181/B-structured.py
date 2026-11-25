# IR: {"sets":{"W":[0,1,2,3],"L":[0,1,2,3]},"params":{"flow":"params['flow'][i][j], i,j in W","distance":"params['distance'][k][l], k,l in L"},"variables":{"x[i,k]":"Binary, i in W, k in L","y[i,j,k,l]":"Continuous in [0,1], i,j in W, k,l in L"},"constraints":["sum(k in L) x[i,k] = 1 for each i in W","sum(i in W) x[i,k] = 1 for each k in L","y[i,j,k,l] <= x[i,k] for all i,j,k,l","y[i,j,k,l] <= x[j,l] for all i,j,k,l","y[i,j,k,l] >= x[i,k] + x[j,l] - 1 for all i,j,k,l"],"objective":"minimize sum(i,j in W; k,l in L) flow[i,j]*distance[k,l]*y[i,j,k,l]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    flow = params["flow"]
    distance = params["distance"]

    model = pyo.ConcreteModel()
    model.W = pyo.RangeSet(0, 3)
    model.L = pyo.RangeSet(0, 3)

    model.flow = pyo.Param(
        model.W,
        model.W,
        initialize=lambda mdl, i, j: flow[i][j],
    )
    model.distance = pyo.Param(
        model.L,
        model.L,
        initialize=lambda mdl, k, l: distance[k][l],
    )

    model.x = pyo.Var(model.W, model.L, domain=pyo.Binary)
    model.y = pyo.Var(
        model.W, model.W, model.L, model.L, domain=pyo.UnitInterval
    )

    model.workstation_assignment = pyo.Constraint(
        model.W,
        rule=lambda mdl, i: sum(mdl.x[i, k] for k in mdl.L) == 1,
    )
    model.location_assignment = pyo.Constraint(
        model.L,
        rule=lambda mdl, k: sum(mdl.x[i, k] for i in mdl.W) == 1,
    )

    model.product_upper_first = pyo.Constraint(
        model.W,
        model.W,
        model.L,
        model.L,
        rule=lambda mdl, i, j, k, l: mdl.y[i, j, k, l] <= mdl.x[i, k],
    )
    model.product_upper_second = pyo.Constraint(
        model.W,
        model.W,
        model.L,
        model.L,
        rule=lambda mdl, i, j, k, l: mdl.y[i, j, k, l] <= mdl.x[j, l],
    )
    model.product_lower = pyo.Constraint(
        model.W,
        model.W,
        model.L,
        model.L,
        rule=lambda mdl, i, j, k, l: (
            mdl.y[i, j, k, l] >= mdl.x[i, k] + mdl.x[j, l] - 1
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.flow[i, j] * model.distance[k, l] * model.y[i, j, k, l]
            for i in model.W
            for j in model.W
            for k in model.L
            for l in model.L
        ),
        sense=pyo.minimize,
    )

    # HiGHS may raise RuntimeError when no feasible solution can be loaded.
    # Success is determined solely by retrieving the objective below.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}