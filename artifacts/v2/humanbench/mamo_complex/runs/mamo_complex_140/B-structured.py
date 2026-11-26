# IR: {"sets":{"V":[1,2,3,4,5,6],"A":"{(i,j) in V x V: i != j}","U":"V minus {1}"},"params":{"cost_matrix":"Required params['cost_matrix']; 6x6 matrix; [i-1][j-1] is the directed travel cost"},"variables":{"x[i,j]":"Binary for (i,j) in A","u[i]":"Real in [1,5] for i in U"},"constraints":["For each i in V: sum(x[i,j] for j in V if j != i) = 1","For each j in V: sum(x[i,j] for i in V if i != j) = 1","For distinct i,j in U: u[i] - u[j] + 6*x[i,j] <= 5"],"objective":"Minimize sum(cost_matrix[i-1][j-1]*x[i,j] for (i,j) in A)","failure_handling":"Return missing_cost_matrix if the required input is absent; otherwise determine success solely by objective retrieval after the solve attempt"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    if "cost_matrix" not in params:
        return {"objective": None, "status": "missing_cost_matrix"}

    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=range(1, 7), ordered=True)
    model.nonorigin_cities = pyo.Set(initialize=range(2, 7), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(1, 7)
            for j in range(1, 7)
            if i != j
        ],
    )

    model.travel_cost = pyo.Param(
        model.arcs,
        initialize={
            (i, j): cost_matrix[i - 1][j - 1]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.nonorigin_cities,
        domain=pyo.Reals,
        bounds=(1, 5),
    )

    def outgoing_rule(instance, i):
        return sum(
            instance.x[i, j]
            for j in instance.cities
            if j != i
        ) == 1

    def incoming_rule(instance, j):
        return sum(
            instance.x[i, j]
            for i in instance.cities
            if i != j
        ) == 1

    def subtour_rule(instance, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return instance.u[i] - instance.u[j] + 6 * instance.x[i, j] <= 5

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)
    model.subtour_elimination = pyo.Constraint(
        model.nonorigin_cities,
        model.nonorigin_cities,
        rule=subtour_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when it cannot load a feasible solution.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}