# IR: {"sets":{"D":[0,1,2,3,4],"S":[0,1,2,3,4],"P":"{(i,j) in D x D: i<j}","A":"{(k,l) in S x S: k!=l}"},"params":{"flow":"flow_01,flow_02,flow_03,flow_04,flow_12,flow_13,flow_14,flow_23,flow_24,flow_34","coord_x":"coord_x0,coord_x1,coord_x2,coord_x3,coord_x4 (site metadata)","coord_y":"coord_y0,coord_y1,coord_y2,coord_y3,coord_y4 (site metadata)","distance":"dist_01,dist_02,dist_03,dist_04,dist_12,dist_13,dist_14,dist_23,dist_24,dist_34 (authoritative rounded distances)"},"variables":{"x[i,k]":"binary, D x S","y[i,j,k,l]":"nonnegative real, P x A"},"constraints":["sum(k in S) x[i,k] = 1 for i in D","sum(i in D) x[i,k] = 1 for k in S","sum(l in S: l!=k) y[i,j,k,l] = x[i,k] for (i,j) in P, k in S","sum(k in S: k!=l) y[i,j,k,l] = x[j,l] for (i,j) in P, l in S"],"objective":"minimize sum((i,j) in P,(k,l) in A) flow[i,j]*distance[min(k,l),max(k,l)]*y[i,j,k,l]; count each division pair once"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    flow_data = {
        (0, 1): params["flow_01"],
        (0, 2): params["flow_02"],
        (0, 3): params["flow_03"],
        (0, 4): params["flow_04"],
        (1, 2): params["flow_12"],
        (1, 3): params["flow_13"],
        (1, 4): params["flow_14"],
        (2, 3): params["flow_23"],
        (2, 4): params["flow_24"],
        (3, 4): params["flow_34"],
    }

    coord_x_data = {
        0: params["coord_x0"],
        1: params["coord_x1"],
        2: params["coord_x2"],
        3: params["coord_x3"],
        4: params["coord_x4"],
    }

    coord_y_data = {
        0: params["coord_y0"],
        1: params["coord_y1"],
        2: params["coord_y2"],
        3: params["coord_y3"],
        4: params["coord_y4"],
    }

    distance_data = {
        (0, 1): params["dist_01"],
        (0, 2): params["dist_02"],
        (0, 3): params["dist_03"],
        (0, 4): params["dist_04"],
        (1, 2): params["dist_12"],
        (1, 3): params["dist_13"],
        (1, 4): params["dist_14"],
        (2, 3): params["dist_23"],
        (2, 4): params["dist_24"],
        (3, 4): params["dist_34"],
    }

    model = pyo.ConcreteModel()

    model.divisions = pyo.RangeSet(0, 4)
    model.sites = pyo.RangeSet(0, 4)
    model.division_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(5)
            for j in range(5)
            if i < j
        ],
    )
    model.site_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (k, ell)
            for k in range(5)
            for ell in range(5)
            if k < ell
        ],
    )
    model.site_arcs = pyo.Set(
        dimen=2,
        initialize=[
            (k, ell)
            for k in range(5)
            for ell in range(5)
            if k != ell
        ],
    )

    model.flow = pyo.Param(
        model.division_pairs,
        initialize=flow_data,
        within=pyo.Reals,
    )
    model.coord_x = pyo.Param(
        model.sites,
        initialize=coord_x_data,
        within=pyo.Reals,
    )
    model.coord_y = pyo.Param(
        model.sites,
        initialize=coord_y_data,
        within=pyo.Reals,
    )
    model.distance = pyo.Param(
        model.site_pairs,
        initialize=distance_data,
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.divisions,
        model.sites,
        domain=pyo.Binary,
    )
    model.y = pyo.Var(
        model.division_pairs,
        model.site_arcs,
        domain=pyo.NonNegativeReals,
    )

    def division_assignment_rule(instance, i):
        return sum(instance.x[i, k] for k in instance.sites) == 1

    model.division_assignment = pyo.Constraint(
        model.divisions,
        rule=division_assignment_rule,
    )

    def site_assignment_rule(instance, k):
        return sum(instance.x[i, k] for i in instance.divisions) == 1

    model.site_assignment = pyo.Constraint(
        model.sites,
        rule=site_assignment_rule,
    )

    # With binary assignments, these marginals force y[i,j,k,l]
    # to equal x[i,k] * x[j,l] without a quadratic objective.
    def first_division_link_rule(instance, i, j, k):
        return (
            sum(
                instance.y[i, j, k, ell]
                for ell in instance.sites
                if ell != k
            )
            == instance.x[i, k]
        )

    model.first_division_link = pyo.Constraint(
        model.division_pairs,
        model.sites,
        rule=first_division_link_rule,
    )

    def second_division_link_rule(instance, i, j, ell):
        return (
            sum(
                instance.y[i, j, k, ell]
                for k in instance.sites
                if k != ell
            )
            == instance.x[j, ell]
        )

    model.second_division_link = pyo.Constraint(
        model.division_pairs,
        model.sites,
        rule=second_division_link_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.flow[i, j]
            * model.distance[min(k, ell), max(k, ell)]
            * model.y[i, j, k, ell]
            for i, j in model.division_pairs
            for k, ell in model.site_arcs
        ),
        sense=pyo.minimize,
    )

    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        # APPsi can raise when no solution is available to load.
        solve_failed = True

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": "solver_failed" if solve_failed else "no_objective",
        }

    return {"objective": obj_val, "status": "optimal"}