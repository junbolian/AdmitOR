# IR: {"sets":{"I":"0..9","J":"0..999","K":"0..4","L":"0..2","M":"0..3"},"params":{"D_jk":"J,K; nonnegative","r_klm":"K,L,M; nonnegative","R_im":"I,M; nonnegative","c_kl":"K,L; nonnegative","c_il":"I,L; nonnegative","P_ikl":"I,K,L; real; unused because the stated objective minimizes transportation costs only","T_ijk":"I,J,K; real"},"input_encoding":"Each parameter accepts a scalar broadcast to all indices, a tuple-keyed mapping, a nested mapping/sequence, or an array.","variables":{"production[i,k,l]":"continuous >= 0","shipment[i,j,k]":"continuous >= 0"},"constraints":["demand[j,k]: sum_i shipment[i,j,k] = D_jk[j,k]","balance[i,k]: sum_l production[i,k,l] = sum_j shipment[i,j,k]","raw_capacity[i,raw]: sum_{k,l} r_klm[k,l,raw]*production[i,k,l] <= R_im[i,raw]","machine_capacity[i,l]: sum_k c_kl[k,l]*production[i,k,l] <= c_il[i,l]"],"objective":"minimize sum_{i,j,k} T_ijk[i,j,k]*shipment[i,j,k]"}

from collections.abc import Mapping
from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _is_scalar(value):
    """Recognize numeric scalars, including zero-dimensional numeric arrays."""
    return isinstance(value, Number) or getattr(value, "ndim", None) == 0


def _scalar_value(value):
    """Convert array scalars to ordinary scalar values when supported."""
    item = getattr(value, "item", None)
    return item() if callable(item) else value


def _entry(data, indices):
    """Read indexed data, broadcasting numeric scalars over remaining indices."""
    if _is_scalar(data):
        return _scalar_value(data)

    if isinstance(data, Mapping):
        if indices in data:
            return _scalar_value(data[indices])
        value = data
        for position in indices:
            if _is_scalar(value):
                return _scalar_value(value)
            value = value[position]
        return _scalar_value(value)

    if isinstance(data, (list, tuple)):
        value = data
        for position in indices:
            if _is_scalar(value):
                return _scalar_value(value)
            value = value[position]
        return _scalar_value(value)

    # Multidimensional arrays support tuple indexing directly.
    return _scalar_value(data[indices])


def solve(params):
    """Build and solve the continuous production and distribution model."""
    demand_data = params["D_jk"]
    raw_requirement_data = params["r_klm"]
    raw_availability_data = params["R_im"]
    time_requirement_data = params["c_kl"]
    time_availability_data = params["c_il"]
    production_cost_data = params["P_ikl"]
    transportation_cost_data = params["T_ijk"]

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 9)
    model.J = pyo.RangeSet(0, 999)
    model.K = pyo.RangeSet(0, 4)
    model.L = pyo.RangeSet(0, 2)
    model.M = pyo.RangeSet(0, 3)

    model.D_jk = pyo.Param(
        model.J,
        model.K,
        initialize=lambda mdl, customer, paper: _entry(
            demand_data, (customer, paper)
        ),
        within=pyo.NonNegativeReals,
    )
    model.r_klm = pyo.Param(
        model.K,
        model.L,
        model.M,
        initialize=lambda mdl, paper, machine, raw: _entry(
            raw_requirement_data, (paper, machine, raw)
        ),
        within=pyo.NonNegativeReals,
    )
    model.R_im = pyo.Param(
        model.I,
        model.M,
        initialize=lambda mdl, mill, raw: _entry(
            raw_availability_data, (mill, raw)
        ),
        within=pyo.NonNegativeReals,
    )
    model.c_kl = pyo.Param(
        model.K,
        model.L,
        initialize=lambda mdl, paper, machine: _entry(
            time_requirement_data, (paper, machine)
        ),
        within=pyo.NonNegativeReals,
    )
    model.c_il = pyo.Param(
        model.I,
        model.L,
        initialize=lambda mdl, mill, machine: _entry(
            time_availability_data, (mill, machine)
        ),
        within=pyo.NonNegativeReals,
    )
    model.P_ikl = pyo.Param(
        model.I,
        model.K,
        model.L,
        initialize=lambda mdl, mill, paper, machine: _entry(
            production_cost_data, (mill, paper, machine)
        ),
        within=pyo.Reals,
    )
    model.T_ijk = pyo.Param(
        model.I,
        model.J,
        model.K,
        initialize=lambda mdl, mill, customer, paper: _entry(
            transportation_cost_data, (mill, customer, paper)
        ),
        within=pyo.Reals,
    )

    model.production = pyo.Var(
        model.I, model.K, model.L, domain=pyo.NonNegativeReals
    )
    model.shipment = pyo.Var(
        model.I, model.J, model.K, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, customer, paper):
        return (
            pyo.quicksum(
                mdl.shipment[mill, customer, paper] for mill in mdl.I
            )
            == mdl.D_jk[customer, paper]
        )

    model.demand = pyo.Constraint(model.J, model.K, rule=demand_rule)

    def balance_rule(mdl, mill, paper):
        return (
            pyo.quicksum(
                mdl.production[mill, paper, machine] for machine in mdl.L
            )
            == pyo.quicksum(
                mdl.shipment[mill, customer, paper] for customer in mdl.J
            )
        )

    model.balance = pyo.Constraint(model.I, model.K, rule=balance_rule)

    def raw_capacity_rule(mdl, mill, raw):
        return (
            pyo.quicksum(
                mdl.r_klm[paper, machine, raw]
                * mdl.production[mill, paper, machine]
                for paper in mdl.K
                for machine in mdl.L
            )
            <= mdl.R_im[mill, raw]
        )

    model.raw_capacity = pyo.Constraint(
        model.I, model.M, rule=raw_capacity_rule
    )

    def machine_capacity_rule(mdl, mill, machine):
        return (
            pyo.quicksum(
                mdl.c_kl[paper, machine]
                * mdl.production[mill, paper, machine]
                for paper in mdl.K
            )
            <= mdl.c_il[mill, machine]
        )

    model.machine_capacity = pyo.Constraint(
        model.I, model.L, rule=machine_capacity_rule
    )

    model.total_transportation_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.T_ijk[mill, customer, paper]
            * model.shipment[mill, customer, paper]
            for mill in model.I
            for customer in model.J
            for paper in model.K
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_transportation_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}