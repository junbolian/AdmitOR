# IR: {"sets":{"V":[0,1,2,3,4],"R":[1,2,3,4],"A":"{(i,j) in V x V: i != j}"},"params":{"cost_matrix":"Input 5x5 matrix indexed in warehouse order A,B,C,D,E; diagonal unused"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"continuous in [1,4] for i in R"},"constraints":["For each i in V: sum(x[i,j] for j != i) = 1","For each j in V: sum(x[i,j] for i != j) = 1","For distinct i,j in R: u[i] - u[j] + 5*x[i,j] <= 4"],"objective":"Minimize sum(cost_matrix[i][j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()

    # Warehouse indices 0 through 4 correspond to A through E.
    model.warehouses = pyo.RangeSet(0, 4)
    model.nonroot_warehouses = pyo.RangeSet(1, 4)
    model.travel_arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.warehouses
            for j in model.warehouses
            if i != j
        ],
    )

    model.travel_cost = pyo.Param(
        model.travel_arcs,
        initialize={
            (i, j): float(cost_matrix[i][j])
            for i, j in model.travel_arcs
        },
        within=pyo.Reals,
    )

    model.route_arc = pyo.Var(model.travel_arcs, domain=pyo.Binary)
    model.visit_order = pyo.Var(
        model.nonroot_warehouses,
        domain=pyo.Reals,
        bounds=(1, 4),
    )

    def outgoing_rule(instance, i):
        return sum(
            instance.route_arc[i, j]
            for j in instance.warehouses
            if j != i
        ) == 1

    model.one_departure = pyo.Constraint(
        model.warehouses,
        rule=outgoing_rule,
    )

    def incoming_rule(instance, j):
        return sum(
            instance.route_arc[i, j]
            for i in instance.warehouses
            if i != j
        ) == 1

    model.one_arrival = pyo.Constraint(
        model.warehouses,
        rule=incoming_rule,
    )

    # Warehouse A is an arbitrary reference point for ordering the tour.
    # Every Hamiltonian cycle contains A, so this does not restrict the route.
    def subtour_rule(instance, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            instance.visit_order[i]
            - instance.visit_order[j]
            + 5 * instance.route_arc[i, j]
            <= 4
        )

    model.subtour_elimination = pyo.Constraint(
        model.nonroot_warehouses,
        model.nonroot_warehouses,
        rule=subtour_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[i, j] * model.route_arc[i, j]
            for i, j in model.travel_arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}