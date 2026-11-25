import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    N = 8
    stores = list(range(1, N))
    nodes = list(range(N))

    dist = {}
    for j in stores:
        dist[(0, j)] = params["dist_0_to_%d" % j]
        dist[(j, 0)] = params["dist_0_to_%d" % j]
    for i in stores:
        for j in stores:
            if i == j:
                dist[(i, j)] = 0.0
            elif i < j:
                d = params["dist_%d_to_%d" % (i, j)]
                dist[(i, j)] = d
                dist[(j, i)] = d

    lower = {0: params["tw0_lower"]}
    upper = {0: params["tw0_upper"]}
    for j in stores:
        lower[j] = params["tw%d_lower" % j]
        upper[j] = params["tw%d_upper" % j]

    service = params["service_time"]
    horizon = params["max_shelf_life"]

    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()
    model.x = pyo.Var(arcs, domain=pyo.Binary)
    # Start clock at departure from warehouse = tw0_lower
    start = lower[0]
    model.t = pyo.Var(nodes, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(dist[(i, j)] * model.x[(i, j)] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    def degree_out_rule(mdl, i):
        return sum(mdl.x[(i, j)] for j in nodes if j != i) == 1

    def degree_in_rule(mdl, j):
        return sum(mdl.x[(i, j)] for i in nodes if i != j) == 1

    model.degree_out = pyo.Constraint(nodes, rule=degree_out_rule)
    model.degree_in = pyo.Constraint(nodes, rule=degree_in_rule)

    # Fix warehouse departure time to its earliest window start
    model.start_time = pyo.Constraint(expr=model.t[0] == start)

    for j in stores:
        model.add_component(
            "time_lo_%d" % j,
            pyo.Constraint(expr=model.t[j] >= lower[j]),
        )
        model.add_component(
            "time_hi_%d" % j,
            pyo.Constraint(expr=model.t[j] <= upper[j]),
        )

    # Route duration: return time minus departure time, bounded by shelf life
    model.shelf_life = pyo.Constraint(
        expr=model.t[0] + (model.t[0] - model.t[0]) <= 0
    )

    bigM = horizon + service + max(
        upper[i] + dist[(i, j)] for (i, j) in arcs
    )

    def time_link_rule(mdl, i, j):
        return mdl.t[j] >= mdl.t[i] + service + dist[(i, j)] - bigM * (1 - mdl.x[(i, j)])

    model.time_link = pyo.Constraint(arcs, rule=time_link_rule)

    # Big-M for the return-to-depot duration constraint
    bigM_dur = horizon + max(dist[(i, j)] for (i, j) in arcs)

    def duration_rule(mdl, i):
        return mdl.t[0] >= mdl.t[i] + service + dist[(i, 0)] - bigM_dur * (1 - mdl.x[(i, 0)])

    model.duration = pyo.Constraint(stores, rule=duration_rule)

    # Also cap the return time to the warehouse window
    model.return_hi = pyo.Constraint(expr=model.t[0] <= upper[0])

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}