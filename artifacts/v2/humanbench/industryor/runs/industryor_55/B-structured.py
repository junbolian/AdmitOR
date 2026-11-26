# IR: {"sets":{"I":"range(len(params['a']))","J":"range(len(params['b']))","K":"range(len(params['f']))"},"params":{"a":"supply[I]","b":"demand[J]","f":"fixed_cost[K]","q":"capacity[K]","c_ik":"inbound_cost[I][K]","c_kj":"outbound_cost[K][J]"},"variables":{"x[I,K]":"continuous >= 0","z[K,J]":"continuous >= 0","y[K]":"binary"},"constraints":["sum_k x[i,k] <= a[i] for each i","sum_k z[k,j] == b[j] for each j","sum_i x[i,k] == sum_j z[k,j] for each k","sum_j z[k,j] <= q[k]*y[k] for each k"],"objective":"minimize sum_i,k c_ik[i][k]*x[i,k] + sum_k,j c_kj[k][j]*z[k,j] + sum_k f[k]*y[k]","input_validation":"Return failure for missing required parameters or inconsistent array dimensions; never invent missing data."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based vectors and nested zero-based cost matrices."""
    required = ("a", "b", "f", "q", "c_ik", "c_kj")
    missing = [key for key in required if key not in params]
    if missing:
        return {
            "objective": None,
            "status": "missing_parameters:" + ",".join(missing),
        }

    a = params["a"]
    b = params["b"]
    f = params["f"]
    q = params["q"]
    c_ik = params["c_ik"]
    c_kj = params["c_kj"]

    production_count = len(a)
    demand_count = len(b)
    station_count = len(f)

    if (
        len(q) != station_count
        or len(c_ik) != production_count
        or len(c_kj) != station_count
        or any(len(row) != station_count for row in c_ik)
        or any(len(row) != demand_count for row in c_kj)
    ):
        return {"objective": None, "status": "invalid_dimensions"}

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=range(production_count), ordered=True)
    model.J = pyo.Set(initialize=range(demand_count), ordered=True)
    model.K = pyo.Set(initialize=range(station_count), ordered=True)

    model.supply = pyo.Param(
        model.I, initialize={i: a[i] for i in model.I}
    )
    model.demand = pyo.Param(
        model.J, initialize={j: b[j] for j in model.J}
    )
    model.fixed_cost = pyo.Param(
        model.K, initialize={k: f[k] for k in model.K}
    )
    model.capacity = pyo.Param(
        model.K, initialize={k: q[k] for k in model.K}
    )
    model.inbound_cost = pyo.Param(
        model.I,
        model.K,
        initialize={
            (i, k): c_ik[i][k]
            for i in model.I
            for k in model.K
        },
    )
    model.outbound_cost = pyo.Param(
        model.K,
        model.J,
        initialize={
            (k, j): c_kj[k][j]
            for k in model.K
            for j in model.J
        },
    )

    model.x = pyo.Var(model.I, model.K, domain=pyo.NonNegativeReals)
    model.z = pyo.Var(model.K, model.J, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.K, domain=pyo.Binary)

    # Tuple constraints also handle empty index sets.
    def supply_constraint(block, i):
        return (
            None,
            pyo.quicksum(block.x[i, k] for k in block.K),
            block.supply[i],
        )

    def demand_constraint(block, j):
        return (
            block.demand[j],
            pyo.quicksum(block.z[k, j] for k in block.K),
            block.demand[j],
        )

    def balance_constraint(block, k):
        return (
            0,
            pyo.quicksum(block.x[i, k] for i in block.I)
            - pyo.quicksum(block.z[k, j] for j in block.J),
            0,
        )

    def capacity_constraint(block, k):
        return (
            None,
            pyo.quicksum(block.z[k, j] for j in block.J)
            - block.capacity[k] * block.y[k],
            0,
        )

    model.supply_limits = pyo.Constraint(model.I, rule=supply_constraint)
    model.demand_requirements = pyo.Constraint(
        model.J, rule=demand_constraint
    )
    model.station_balance = pyo.Constraint(
        model.K, rule=balance_constraint
    )
    model.station_capacity = pyo.Constraint(
        model.K, rule=capacity_constraint
    )

    model.total_cost = pyo.Objective(
        expr=(
            pyo.quicksum(
                model.inbound_cost[i, k] * model.x[i, k]
                for i in model.I
                for k in model.K
            )
            + pyo.quicksum(
                model.outbound_cost[k, j] * model.z[k, j]
                for k in model.K
                for j in model.J
            )
            + pyo.quicksum(
                model.fixed_cost[k] * model.y[k] for k in model.K
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}