import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    installation_cost = params["installation_cost"]
    distance_matrix = params["distance_matrix"]
    basic_radius_R1 = params["basic_radius_R1"]
    premium_radius_R2 = params["premium_radius_R2"]
    premium_bonus = params["premium_bonus"]

    n_clients = len(premium_bonus)
    n_facilities = len(installation_cost)

    clients = list(range(n_clients))
    facilities = list(range(n_facilities))

    # Basic coverage: client i can be served by facility j if distance <= R1
    basic_cover = {
        (i, j): distance_matrix[i][j] <= basic_radius_R1
        for i in clients for j in facilities
    }
    # Premium eligibility: client i is premium if some open facility j has distance <= R2
    premium_cover = {
        (i, j): distance_matrix[i][j] <= premium_radius_R2
        for i in clients for j in facilities
    }

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=clients)
    model.J = pyo.Set(initialize=facilities)

    model.y = pyo.Var(model.J, domain=pyo.Binary)  # open facility
    model.z = pyo.Var(model.I, domain=pyo.Binary)  # premium served

    # Every household must be covered by at least one open facility within R1
    model.basic_cover_con = pyo.Constraint(
        model.I,
        rule=lambda m, i: sum(m.y[j] for j in m.J if basic_cover[(i, j)]) >= 1
    )

    # Client is premium only if at least one open facility within R2
    model.premium_con = pyo.Constraint(
        model.I,
        rule=lambda m, i: m.z[i] <= sum(m.y[j] for j in m.J if premium_cover[(i, j)])
    )

    model.obj = pyo.Objective(
        expr=sum(installation_cost[j] * model.y[j] for j in model.J)
             - sum(premium_bonus[i] * model.z[i] for i in model.I),
        sense=pyo.minimize
    )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}