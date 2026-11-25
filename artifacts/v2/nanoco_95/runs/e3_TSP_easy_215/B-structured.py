# IR: {"sets":{"N":"{0,...,8}","C":"N\\{0}","A":"{(i,j) in N x N:i!=j}","P":"{(i,j) in C x C:i!=j}","D":"{0,1}"},"params":{"distance_matrix":"nonnegative 9x9 matrix","node0_coords":"coordinate pair","node1_coords":"coordinate pair","node2_coords":"coordinate pair","node3_coords":"coordinate pair","node4_coords":"coordinate pair","node5_coords":"coordinate pair","node6_coords":"coordinate pair","node7_coords":"coordinate pair","node8_coords":"coordinate pair","distance[i,j]":"distance_matrix[i][j]","coordinates[i,k]":"node{i}_coords[k]; descriptive data only","q":"|C|"},"variables":{"x[i,j]":"binary, (i,j) in A","u[i]":"continuous, 1<=u[i]<=q, i in C"},"constraints":["For each i in N: sum(x[i,j] for j in N if j!=i)=1","For each j in N: sum(x[i,j] for i in N if i!=j)=1","For each (i,j) in P: u[i]-u[j]+q*x[i,j]<=q-1"],"objective":"minimize sum(distance[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    coordinate_data = {
        0: params["node0_coords"],
        1: params["node1_coords"],
        2: params["node2_coords"],
        3: params["node3_coords"],
        4: params["node4_coords"],
        5: params["node5_coords"],
        6: params["node6_coords"],
        7: params["node7_coords"],
        8: params["node8_coords"],
    }

    model = pyo.ConcreteModel()

    model.N = pyo.RangeSet(0, 8)
    model.C = pyo.RangeSet(1, 8)
    model.D = pyo.RangeSet(0, 1)
    model.A = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.N
            for j in model.N
            if i != j
        ],
    )
    model.P = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.C
            for j in model.C
            if i != j
        ],
    )

    model.distance = pyo.Param(
        model.N,
        model.N,
        initialize={
            (i, j): distance_matrix[i][j]
            for i in model.N
            for j in model.N
        },
        within=pyo.NonNegativeReals,
    )
    model.coordinates = pyo.Param(
        model.N,
        model.D,
        initialize={
            (i, k): coordinate_data[i][k]
            for i in model.N
            for k in model.D
        },
        within=pyo.Reals,
    )
    model.q = pyo.Param(
        initialize=len(model.C),
        within=pyo.PositiveIntegers,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(
        model.C,
        domain=pyo.Reals,
        bounds=(1, len(model.C)),
    )

    def outgoing_rule(mdl, i):
        return sum(
            mdl.x[i, j] for j in mdl.N if j != i
        ) == 1

    model.outgoing = pyo.Constraint(
        model.N,
        rule=outgoing_rule,
    )

    def incoming_rule(mdl, j):
        return sum(
            mdl.x[i, j] for i in mdl.N if i != j
        ) == 1

    model.incoming = pyo.Constraint(
        model.N,
        rule=incoming_rule,
    )

    def subtour_rule(mdl, i, j):
        return (
            mdl.u[i] - mdl.u[j] + mdl.q * mdl.x[i, j]
            <= mdl.q - 1
        )

    model.subtour = pyo.Constraint(
        model.P,
        rule=subtour_rule,
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.distance[i, j] * model.x[i, j]
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}