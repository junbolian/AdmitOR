# IR: {"sets":{"V":"{0,...,15}","H":"V\\{0}","A":"{(i,j): i in V, j in H, i != j}"},"params":{"port_limit":"params['port_limit']","cost_matrix":"params['cost_matrix'], symmetric 16x16 matrix","N":"|H|"},"variables":{"x[i,j]":"binary for (i,j) in A; selects parent-to-child link","f[i,j]":"nonnegative real for (i,j) in A; number of subscribers served downstream"},"constraints":["For each j in H: sum(i: (i,j) in A) x[i,j] = 1.","For each j in H: sum(i: (i,j) in A) f[i,j] - sum(k: (j,k) in A) f[j,k] = 1.","sum(j in H) f[0,j] = N.","For each (i,j) in A: f[i,j] <= (port_limit if i=0 else N)*x[i,j]."],"objective":"Minimize sum((i,j) in A) cost_matrix[i][j]*x[i,j]."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    port_limit = params["port_limit"]
    cost_matrix = params["cost_matrix"]

    vertices = tuple(range(16))
    homes = tuple(range(1, 16))
    arcs = tuple(
        (source, target)
        for source in vertices
        for target in homes
        if source != target
    )
    subscriber_count = len(homes)

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=vertices, ordered=True)
    model.H = pyo.Set(initialize=homes, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.port_limit = pyo.Param(
        initialize=port_limit,
        within=pyo.Reals,
    )
    model.link_cost = pyo.Param(
        model.A,
        initialize={
            (source, target): cost_matrix[source][target]
            for source, target in arcs
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.f = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def one_parent_rule(instance, target):
        return sum(
            instance.x[source, target]
            for source in instance.V
            if source != target
        ) == 1

    model.one_parent = pyo.Constraint(model.H, rule=one_parent_rule)

    def flow_balance_rule(instance, target):
        incoming = sum(
            instance.f[source, target]
            for source in instance.V
            if source != target
        )
        outgoing = sum(
            instance.f[target, child]
            for child in instance.H
            if child != target
        )
        return incoming - outgoing == 1

    model.flow_balance = pyo.Constraint(
        model.H,
        rule=flow_balance_rule,
    )

    model.root_supply = pyo.Constraint(
        expr=sum(model.f[0, target] for target in model.H)
        == subscriber_count
    )

    def arc_capacity_rule(instance, source, target):
        capacity = (
            instance.port_limit if source == 0 else subscriber_count
        )
        return (
            instance.f[source, target]
            <= capacity * instance.x[source, target]
        )

    model.arc_capacity = pyo.Constraint(
        model.A,
        rule=arc_capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.link_cost[source, target] * model.x[source, target]
            for source, target in model.A
        ),
        sense=pyo.minimize,
    )

    # Single-parent constraints and flow conservation enforce a rooted tree.
    # Root-arc flow equals its complete downstream subtree's node count.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}