# IR: {"sets":{"V":"{0,...,15}","H":"{1,...,15}","E":"{(i,j): i,j in V, i<j}","A":"{(i,j): i in V, j in H, i!=j}"},"params":{"capacity":"params['splitter_port_limit']","cost[i,j]":"params['dist_<i>_<j>'] for (i,j) in E"},"variables":{"x[i,j]":"Binary for (i,j) in A; selected parent-to-child arc","flow[i,j]":"NonNegativeReals for (i,j) in A; number of subscribers downstream"},"constraints":["For each j in H: sum(x[i,j] for i in V if i!=j)=1","For each j in H: sum(flow[i,j] for i in V if i!=j)-sum(flow[j,k] for k in H if k!=j)=1","sum(flow[0,j] for j in H)=|H|","For each (i,j) in A: flow[i,j]>=x[i,j]","For each (i,j) in A: flow[i,j]<=capacity*x[i,j]"],"objective":"Minimize sum(cost[min(i,j),max(i,j)]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.V = pyo.RangeSet(0, 15)
    model.H = pyo.RangeSet(1, 15)

    model.E = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(16)
            for j in range(i + 1, 16)
        ],
    )
    model.A = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(16)
            for j in range(1, 16)
            if i != j
        ],
    )

    model.capacity = pyo.Param(
        initialize=params["splitter_port_limit"],
        within=pyo.Reals,
    )
    model.cost = pyo.Param(
        model.E,
        initialize={
            (i, j): params[f"dist_{i}_{j}"]
            for i, j in model.E
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.flow = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def one_parent_rule(mdl, j):
        return sum(
            mdl.x[i, j] for i in mdl.V if i != j
        ) == 1

    model.one_parent = pyo.Constraint(
        model.H,
        rule=one_parent_rule,
    )

    def flow_balance_rule(mdl, j):
        incoming = sum(
            mdl.flow[i, j] for i in mdl.V if i != j
        )
        outgoing = sum(
            mdl.flow[j, k] for k in mdl.H if k != j
        )
        return incoming - outgoing == 1

    model.flow_balance = pyo.Constraint(
        model.H,
        rule=flow_balance_rule,
    )

    model.root_supply = pyo.Constraint(
        expr=sum(model.flow[0, j] for j in model.H) == len(model.H)
    )

    def flow_lower_rule(mdl, i, j):
        return mdl.flow[i, j] >= mdl.x[i, j]

    model.flow_lower = pyo.Constraint(
        model.A,
        rule=flow_lower_rule,
    )

    def flow_upper_rule(mdl, i, j):
        return mdl.flow[i, j] <= mdl.capacity * mdl.x[i, j]

    model.flow_upper = pyo.Constraint(
        model.A,
        rule=flow_upper_rule,
    )

    # Flow conservation excludes subscriber-only cycles. Together with
    # exactly one parent per subscriber, it produces a rooted spanning tree.
    # Each selected arc carries its downstream subscriber count, so limiting
    # every arc's flow also enforces the required feeder-subtree limit.
    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[min(i, j), max(i, j)] * model.x[i, j]
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # APPsi raises this when it cannot load a feasible solution.
        # Propagate unrelated runtime errors.
        if "a feasible solution was not found" in str(error).lower():
            return {"objective": None, "status": "infeasible_or_failed"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}