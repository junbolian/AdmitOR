import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arc_capacity = params["arc_capacity"]
    arc_cost = params["arc_cost"]

    # Arc list in the order given in the problem
    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 7),
        (1, 2), (1, 5),
        (2, 3), (2, 5), (2, 6),
        (3, 4), (3, 5),
        (4, 5), (4, 6), (4, 7),
        (5, 6), (5, 7),
        (6, 7),
    ]
    nodes = list(range(8))
    source = 0
    sink = 7

    # Build dictionaries keyed by arc index
    cap = {i: arc_capacity[i] for i in range(len(arcs))}
    cost = {i: arc_cost[i] for i in range(len(arcs))}

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=range(len(arcs)))
    model.NODES = pyo.Set(initialize=nodes)

    # Flow variables
    model.f = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    # Capacity constraints
    def cap_rule(mdl, i):
        return mdl.f[i] <= cap[i]
    model.cap_con = pyo.Constraint(model.ARCS, rule=cap_rule)

    # Outflow variable = total flow leaving the source
    model.outflow = pyo.Var(domain=pyo.NonNegativeReals)

    def outflow_rule(mdl):
        return mdl.outflow == sum(mdl.f[i] for i in mdl.ARCS if arcs[i][0] == source)
    model.outflow_con = pyo.Constraint(rule=outflow_rule)

    # Flow conservation at each intermediate node
    def cons_rule(mdl, n):
        if n == source or n == sink:
            return pyo.Constraint.Skip
        inflow = sum(mdl.f[i] for i in mdl.ARCS if arcs[i][1] == n)
        outflow = sum(mdl.f[i] for i in mdl.ARCS if arcs[i][0] == n)
        return inflow == outflow
    model.flow_con = pyo.Constraint(model.NODES, rule=cons_rule)

    # Sink balance: inflow to sink equals source outflow
    def sink_rule(mdl):
        inflow_sink = sum(mdl.f[i] for i in mdl.ARCS if arcs[i][1] == sink)
        return inflow_sink == mdl.outflow
    model.sink_con = pyo.Constraint(rule=sink_rule)

    # ------------------------------------------------------------------
    # Stage 1: maximize total flow (lexicographic, first level)
    # ------------------------------------------------------------------
    model.max_flow_obj = pyo.Objective(expr=model.outflow, sense=pyo.maximize)

    Highs().solve(model)

    max_flow_val = float(pyo.value(model.outflow))

    # ------------------------------------------------------------------
    # Stage 2: minimize cost subject to achieving the maximum flow
    # ------------------------------------------------------------------
    # Fix the maximum flow value via the outflow variable
    model.flow_fix = pyo.Constraint(expr=model.outflow >= max_flow_val)

    model.cost_obj = pyo.Objective(
        expr=sum(cost[i] * model.f[i] for i in model.ARCS),
        sense=pyo.minimize,
    )
    model.max_flow_obj.deactivate()

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost_obj))
    return {"objective": obj_val, "status": "optimal"}