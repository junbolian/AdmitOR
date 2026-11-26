# IR: {"sets":[],"params":["cereal_capacity","meat_capacity","cereal_cost_per_lb","meat_cost_per_lb","meaties_price","yummies_price","meaties_cereal_per_pkg","meaties_meat_per_pkg","yummies_cereal_per_pkg","yummies_meat_per_pkg","meaties_blend_pack_cost","yummies_blend_pack_cost","meaties_machine_capacity"],"variables":{"meaties_qty":"NonNegativeReals","yummies_qty":"NonNegativeReals"},"constraints":["meaties_cereal_per_pkg*meaties_qty+yummies_cereal_per_pkg*yummies_qty<=cereal_capacity","meaties_meat_per_pkg*meaties_qty+yummies_meat_per_pkg*yummies_qty<=meat_capacity","meaties_qty<=meaties_machine_capacity"],"objective":"maximize (meaties_price-cereal_cost_per_lb*meaties_cereal_per_pkg-meat_cost_per_lb*meaties_meat_per_pkg-meaties_blend_pack_cost)*meaties_qty+(yummies_price-cereal_cost_per_lb*yummies_cereal_per_pkg-meat_cost_per_lb*yummies_meat_per_pkg-yummies_blend_pack_cost)*yummies_qty"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.cereal_capacity = pyo.Param(
        initialize=params["cereal_capacity"]
    )
    model.meat_capacity = pyo.Param(
        initialize=params["meat_capacity"]
    )
    model.cereal_cost_per_lb = pyo.Param(
        initialize=params["cereal_cost_per_lb"]
    )
    model.meat_cost_per_lb = pyo.Param(
        initialize=params["meat_cost_per_lb"]
    )
    model.meaties_price = pyo.Param(
        initialize=params["meaties_price"]
    )
    model.yummies_price = pyo.Param(
        initialize=params["yummies_price"]
    )
    model.meaties_cereal_per_pkg = pyo.Param(
        initialize=params["meaties_cereal_per_pkg"]
    )
    model.meaties_meat_per_pkg = pyo.Param(
        initialize=params["meaties_meat_per_pkg"]
    )
    model.yummies_cereal_per_pkg = pyo.Param(
        initialize=params["yummies_cereal_per_pkg"]
    )
    model.yummies_meat_per_pkg = pyo.Param(
        initialize=params["yummies_meat_per_pkg"]
    )
    model.meaties_blend_pack_cost = pyo.Param(
        initialize=params["meaties_blend_pack_cost"]
    )
    model.yummies_blend_pack_cost = pyo.Param(
        initialize=params["yummies_blend_pack_cost"]
    )
    model.meaties_machine_capacity = pyo.Param(
        initialize=params["meaties_machine_capacity"]
    )

    model.meaties_qty = pyo.Var(domain=pyo.NonNegativeReals)
    model.yummies_qty = pyo.Var(domain=pyo.NonNegativeReals)

    model.cereal_limit = pyo.Constraint(
        expr=(
            model.meaties_cereal_per_pkg * model.meaties_qty
            + model.yummies_cereal_per_pkg * model.yummies_qty
            <= model.cereal_capacity
        )
    )
    model.meat_limit = pyo.Constraint(
        expr=(
            model.meaties_meat_per_pkg * model.meaties_qty
            + model.yummies_meat_per_pkg * model.yummies_qty
            <= model.meat_capacity
        )
    )
    model.meaties_machine_limit = pyo.Constraint(
        expr=model.meaties_qty <= model.meaties_machine_capacity
    )

    model.profit = pyo.Objective(
        expr=(
            (
                model.meaties_price
                - model.cereal_cost_per_lb * model.meaties_cereal_per_pkg
                - model.meat_cost_per_lb * model.meaties_meat_per_pkg
                - model.meaties_blend_pack_cost
            )
            * model.meaties_qty
            + (
                model.yummies_price
                - model.cereal_cost_per_lb * model.yummies_cereal_per_pkg
                - model.meat_cost_per_lb * model.yummies_meat_per_pkg
                - model.yummies_blend_pack_cost
            )
            * model.yummies_qty
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Propagate unrelated errors instead of hiding unexpected failures.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}