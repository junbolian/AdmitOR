# IR: {"sets":{"K":"1..num_vehicles","V":"0..num_customers","C":"1..num_customers","A":"{(i,j) in V x V: i != j}","P":"{(i,j) in C x C: i != j}"},"params":{"num_vehicles":"positive integer; frozen set size","num_customers":"positive integer; frozen set size","depot_x":"real; facility coordinate metadata","depot_y":"real; facility coordinate metadata","coord_x":"real[V]; coordinate metadata","coord_y":"real[V]; coordinate metadata","distance_matrix":"nonnegative real[V,V]; authoritative arc costs"},"variables":{"x[k,i,j]":"binary, k in K, (i,j) in A","u[k,i]":"continuous in [1,num_customers], k in K, i in C"},"constraints":{"visit_once":"sum(k in K, j in V excluding i) x[k,i,j] = 1 for i in C","customer_flow":"sum(j in V excluding i) x[k,i,j] = sum(j in V excluding i) x[k,j,i] for k in K, i in C","depot_departure":"sum(j in C) x[k,0,j] = 1 for k in K","depot_return":"sum(i in C) x[k,i,0] = 1 for k in K","subtour_elimination":"u[k,i] - u[k,j] + num_customers*x[k,i,j] <= num_customers - 1 for k in K, (i,j) in P"},"objective":"minimize sum(k in K, (i,j) in A) distance_matrix[i,j]*x[k,i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_vehicles = params["num_vehicles"]
    num_customers = params["num_customers"]
    depot_x = params["depot_x"]
    depot_y = params["depot_y"]
    coord_x = params["coord_x"]
    coord_y = params["coord_y"]
    distance_matrix = params["distance_matrix"]

    model = pyo.ConcreteModel()

    model.vehicle_count = pyo.Param(
        initialize=num_vehicles, within=pyo.PositiveIntegers
    )
    model.customer_count = pyo.Param(
        initialize=num_customers, within=pyo.PositiveIntegers
    )

    model.K = pyo.RangeSet(1, num_vehicles)
    model.V = pyo.RangeSet(0, num_customers)
    model.C = pyo.RangeSet(1, num_customers)
    model.A = pyo.Set(
        dimen=2,
        initialize=(
            (i, j)
            for i in range(num_customers + 1)
            for j in range(num_customers + 1)
            if i != j
        ),
    )
    model.P = pyo.Set(
        dimen=2,
        initialize=(
            (i, j)
            for i in range(1, num_customers + 1)
            for j in range(1, num_customers + 1)
            if i != j
        ),
    )

    # Coordinates are metadata; supplied matrix entries determine route costs.
    model.facility_x = pyo.Param(initialize=depot_x, within=pyo.Reals)
    model.facility_y = pyo.Param(initialize=depot_y, within=pyo.Reals)
    model.node_x = pyo.Param(
        model.V,
        initialize=lambda mdl, i: coord_x[i],
        within=pyo.Reals,
    )
    model.node_y = pyo.Param(
        model.V,
        initialize=lambda mdl, i: coord_y[i],
        within=pyo.Reals,
    )
    model.distance = pyo.Param(
        model.V,
        model.V,
        initialize=lambda mdl, i, j: distance_matrix[i][j],
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.K, model.A, domain=pyo.Binary)
    model.u = pyo.Var(
        model.K,
        model.C,
        domain=pyo.Reals,
        bounds=(1, num_customers),
    )

    def visit_once_rule(mdl, i):
        return pyo.quicksum(
            mdl.x[k, i, j]
            for k in mdl.K
            for j in mdl.V
            if j != i
        ) == 1

    model.visit_once = pyo.Constraint(model.C, rule=visit_once_rule)

    def customer_flow_rule(mdl, k, i):
        return pyo.quicksum(
            mdl.x[k, i, j] for j in mdl.V if j != i
        ) == pyo.quicksum(
            mdl.x[k, j, i] for j in mdl.V if j != i
        )

    model.customer_flow = pyo.Constraint(
        model.K, model.C, rule=customer_flow_rule
    )

    def depot_departure_rule(mdl, k):
        return pyo.quicksum(mdl.x[k, 0, j] for j in mdl.C) == 1

    model.depot_departure = pyo.Constraint(
        model.K, rule=depot_departure_rule
    )

    def depot_return_rule(mdl, k):
        return pyo.quicksum(mdl.x[k, i, 0] for i in mdl.C) == 1

    model.depot_return = pyo.Constraint(model.K, rule=depot_return_rule)

    def subtour_elimination_rule(mdl, k, i, j):
        return (
            mdl.u[k, i]
            - mdl.u[k, j]
            + mdl.customer_count * mdl.x[k, i, j]
            <= mdl.customer_count - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.K, model.P, rule=subtour_elimination_rule
    )

    model.total_distance = pyo.Objective(
        expr=pyo.quicksum(
            model.distance[i, j] * model.x[k, i, j]
            for k in model.K
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    # APPsi may raise RuntimeError when no solution can be loaded.
    # Leave unexpected RuntimeErrors visible to the caller.
    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise

    # Objective retrieval is the sole test for success.
    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}