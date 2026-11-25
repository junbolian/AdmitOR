# IR: {"sets":{"N":"{0,...,7}","C":"{1,...,7}","A":"{(i,j) in N x N: i!=j}"},"params":{"t[i,j]":"params['travel_time'][i][j]","e[i]":"params['tw_<i>_earliest'] for i in N","l[i]":"params['tw_<i>_latest'] for i in N","s":"params['service_time']","H":"params['max_shelf_life_window']","M[i,j]":"max(0,l[i]+s+t[i,j]-e[j])"},"variables":{"x[i,j]":"Binary for (i,j) in A","a[i]":"Real in [e[i],l[i]] for i in C; service-start time","d":"Real in [e[0],l[0]]; depot service-start time","r":"Real in [e[0],l[0]]; depot return time","u[i]":"Real in [1,7] for i in C"},"constraints":["sum(j!=i)x[i,j]=1 for i in N","sum(i!=j)x[i,j]=1 for j in N","u[i]-u[j]+7*x[i,j]<=6 for distinct i,j in C","a[j]>=d+s+t[0,j]-M[0,j]*(1-x[0,j]) for j in C","a[j]>=a[i]+s+t[i,j]-M[i,j]*(1-x[i,j]) for distinct i,j in C","r>=a[i]+s+t[i,0]-M[i,0]*(1-x[i,0]) for i in C","r>=d","r-d<=H"],"objective":"minimize sum((i,j) in A)t[i,j]*x[i,j]"}
# Time windows use inclusive earliest/latest service-start bounds.
# Waiting is allowed. Depot service occurs before departure; return completes
# the route without a second depot service operation.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(8))
    stores = tuple(range(1, 8))
    arcs = tuple(
        (origin, destination)
        for origin in nodes
        for destination in nodes
        if origin != destination
    )
    store_arcs = tuple(
        (origin, destination)
        for origin in stores
        for destination in stores
        if origin != destination
    )

    travel_time = params["travel_time"]
    earliest = (
        params["tw_0_earliest"],
        params["tw_1_earliest"],
        params["tw_2_earliest"],
        params["tw_3_earliest"],
        params["tw_4_earliest"],
        params["tw_5_earliest"],
        params["tw_6_earliest"],
        params["tw_7_earliest"],
    )
    latest = (
        params["tw_0_latest"],
        params["tw_1_latest"],
        params["tw_2_latest"],
        params["tw_3_latest"],
        params["tw_4_latest"],
        params["tw_5_latest"],
        params["tw_6_latest"],
        params["tw_7_latest"],
    )
    service_time = params["service_time"]
    shelf_life = params["max_shelf_life_window"]

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.C = pyo.Set(initialize=stores, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.CA = pyo.Set(dimen=2, initialize=store_arcs, ordered=True)

    model.t = pyo.Param(
        model.A,
        initialize={
            (origin, destination): travel_time[origin][destination]
            for origin, destination in arcs
        },
        within=pyo.NonNegativeReals,
    )
    model.e = pyo.Param(
        model.N,
        initialize=dict(enumerate(earliest)),
        within=pyo.Reals,
    )
    model.l = pyo.Param(
        model.N,
        initialize=dict(enumerate(latest)),
        within=pyo.Reals,
    )
    model.s = pyo.Param(
        initialize=service_time,
        within=pyo.NonNegativeReals,
    )
    model.H = pyo.Param(
        initialize=shelf_life,
        within=pyo.NonNegativeReals,
    )
    model.M = pyo.Param(
        model.A,
        initialize=lambda mdl, origin, destination: max(
            0,
            pyo.value(
                mdl.l[origin]
                + mdl.s
                + mdl.t[origin, destination]
                - mdl.e[destination]
            ),
        ),
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.a = pyo.Var(
        model.C,
        domain=pyo.Reals,
        bounds=lambda mdl, store: (mdl.e[store], mdl.l[store]),
    )
    model.d = pyo.Var(
        domain=pyo.Reals,
        bounds=(model.e[0], model.l[0]),
    )
    model.r = pyo.Var(
        domain=pyo.Reals,
        bounds=(model.e[0], model.l[0]),
    )
    model.u = pyo.Var(
        model.C,
        domain=pyo.Reals,
        bounds=(1, len(stores)),
    )

    def outbound_rule(mdl, origin):
        return sum(
            mdl.x[origin, destination]
            for destination in mdl.N
            if destination != origin
        ) == 1

    def inbound_rule(mdl, destination):
        return sum(
            mdl.x[origin, destination]
            for origin in mdl.N
            if origin != destination
        ) == 1

    def subtour_rule(mdl, origin, destination):
        return (
            mdl.u[origin]
            - mdl.u[destination]
            + len(stores) * mdl.x[origin, destination]
            <= len(stores) - 1
        )

    def departure_time_rule(mdl, store):
        return mdl.a[store] >= (
            mdl.d
            + mdl.s
            + mdl.t[0, store]
            - mdl.M[0, store] * (1 - mdl.x[0, store])
        )

    def store_time_rule(mdl, origin, destination):
        return mdl.a[destination] >= (
            mdl.a[origin]
            + mdl.s
            + mdl.t[origin, destination]
            - mdl.M[origin, destination]
            * (1 - mdl.x[origin, destination])
        )

    def return_time_rule(mdl, store):
        return mdl.r >= (
            mdl.a[store]
            + mdl.s
            + mdl.t[store, 0]
            - mdl.M[store, 0] * (1 - mdl.x[store, 0])
        )

    model.outbound = pyo.Constraint(model.N, rule=outbound_rule)
    model.inbound = pyo.Constraint(model.N, rule=inbound_rule)
    model.subtour = pyo.Constraint(model.CA, rule=subtour_rule)
    model.departure_timing = pyo.Constraint(
        model.C, rule=departure_time_rule
    )
    model.store_timing = pyo.Constraint(
        model.CA, rule=store_time_rule
    )
    model.return_timing = pyo.Constraint(
        model.C, rule=return_time_rule
    )
    model.return_after_start = pyo.Constraint(expr=model.r >= model.d)
    model.route_duration = pyo.Constraint(
        expr=model.r - model.d <= model.H
    )

    model.total_travel = pyo.Objective(
        expr=sum(
            model.t[origin, destination] * model.x[origin, destination]
            for origin, destination in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this specific error when no solution can be loaded.
        # Other runtime errors are unexpected and must propagate.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_travel))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}