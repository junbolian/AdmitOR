# IR: {"sets":{"A":"range(asset_count)"},"params":["asset_count","target_return","max_allocation","total_allocation","expected_returns[A]","covariance_matrix[A,A]"],"variables":{"weight[A]":"continuous, 0 <= weight[i] <= max_allocation"},"expressions":{"portfolio_variance":"sum(covariance_matrix[i,j]*weight[i]*weight[j] for i,j in A)"},"constraints":["sum(weight[i] for i in A) == total_allocation","sum(expected_returns[i]*weight[i] for i in A) >= target_return*total_allocation"],"objective":"minimize portfolio_variance","implementation":"Eliminate the variance-definition auxiliary variable exactly; transfer the quadratic objective Hessian to native HiGHS through a temporary APPSI adapter."}

import operator
from unittest.mock import patch

import highspy
import numpy as np
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs
from pyomo.repn import generate_standard_repn


class _HessianTransferError(RuntimeError):
    pass


def solve(params):
    asset_count = operator.index(params["asset_count"])
    target_return = float(params["target_return"])
    max_allocation = float(params["max_allocation"])
    total_allocation = float(params["total_allocation"])
    expected_returns = np.asarray(params["expected_returns"], dtype=float)
    covariance_matrix = np.asarray(params["covariance_matrix"], dtype=float)

    if asset_count <= 0:
        raise ValueError("asset_count must be positive.")
    if expected_returns.shape != (asset_count,):
        raise ValueError("expected_returns must have asset_count entries.")
    if covariance_matrix.shape != (asset_count, asset_count):
        raise ValueError("covariance_matrix must be asset_count by asset_count.")
    if not np.isfinite(
        [target_return, max_allocation, total_allocation]
    ).all():
        raise ValueError("Scalar parameters must be finite.")
    if not np.isfinite(expected_returns).all():
        raise ValueError("expected_returns must contain finite values.")
    if not np.isfinite(covariance_matrix).all():
        raise ValueError("covariance_matrix must contain finite values.")
    if max_allocation < 0:
        raise ValueError("max_allocation must be nonnegative.")
    if total_allocation <= 0:
        raise ValueError("total_allocation must be positive.")

    model = pyo.ConcreteModel()
    model.assets = pyo.Set(initialize=range(asset_count), ordered=True)

    model.required_return = pyo.Param(initialize=target_return)
    model.allocation_cap = pyo.Param(initialize=max_allocation)
    model.allocation_total = pyo.Param(initialize=total_allocation)
    model.asset_returns = pyo.Param(
        model.assets,
        initialize={
            asset: float(expected_returns[asset])
            for asset in range(asset_count)
        },
    )
    model.asset_covariances = pyo.Param(
        model.assets,
        model.assets,
        initialize={
            (first, second): float(covariance_matrix[first, second])
            for first in range(asset_count)
            for second in range(asset_count)
        },
    )

    model.weight = pyo.Var(
        model.assets,
        domain=pyo.NonNegativeReals,
        bounds=(0, max_allocation),
    )

    model.full_allocation = pyo.Constraint(
        expr=sum(model.weight[asset] for asset in model.assets)
        == model.allocation_total
    )
    model.minimum_return = pyo.Constraint(
        expr=sum(
            model.asset_returns[asset] * model.weight[asset]
            for asset in model.assets
        )
        >= model.required_return * model.allocation_total
    )

    model.portfolio_variance = pyo.Expression(
        expr=sum(
            model.asset_covariances[first, second]
            * model.weight[first]
            * model.weight[second]
            for first in model.assets
            for second in model.assets
        )
    )
    model.risk_objective = pyo.Objective(
        expr=model.portfolio_variance,
        sense=pyo.minimize,
    )

    original_set_objective = Highs._set_objective

    def set_quadratic_objective(solver, objective):
        if objective is not model.risk_objective:
            return original_set_objective(solver, objective)

        solver.highs_options["output_flag"] = False
        solver._solver_model.setOptionValue("output_flag", False)

        representation = generate_standard_repn(
            objective.expr,
            quadratic=True,
            compute_values=True,
        )
        if representation.nonlinear_expr is not None:
            raise ValueError("The portfolio objective must be quadratic.")

        # Let APPSI install the objective's constant and linear terms.
        linear_objective = pyo.Objective(
            expr=representation.constant
            + sum(
                coefficient * variable
                for coefficient, variable in zip(
                    representation.linear_coefs,
                    representation.linear_vars,
                )
            ),
            sense=objective.sense,
        )
        linear_objective.construct()
        original_set_objective(solver, linear_objective)

        column_map = solver._pyomo_var_to_solver_var_map
        column_count = len(column_map)
        hessian_columns = [{} for _ in range(column_count)]

        # HiGHS uses 0.5*x.T*H*x. Diagonal polynomial coefficients
        # therefore contribute twice their value to H; cross terms
        # contribute their value once to its stored lower triangle.
        for variables, coefficient in zip(
            representation.quadratic_vars,
            representation.quadratic_coefs,
        ):
            first_column = column_map[id(variables[0])]
            second_column = column_map[id(variables[1])]
            row = max(first_column, second_column)
            column = min(first_column, second_column)
            entry = float(coefficient)
            if first_column == second_column:
                entry *= 2

            entries = hessian_columns[column]
            entries[row] = entries.get(row, 0.0) + entry

        starts = [0]
        row_indices = []
        hessian_values = []

        for entries in hessian_columns:
            for row, entry in sorted(entries.items()):
                if entry != 0:
                    row_indices.append(row)
                    hessian_values.append(entry)
            starts.append(len(row_indices))

        if hessian_values:
            hessian = highspy.HighsHessian()
            hessian.dim_ = column_count
            hessian.format_ = highspy.HessianFormat.kTriangular
            hessian.start_ = np.asarray(starts, dtype=np.int32)
            hessian.index_ = np.asarray(row_indices, dtype=np.int32)
            hessian.value_ = np.asarray(hessian_values, dtype=np.float64)

            transfer_status = solver._solver_model.passHessian(hessian)
            if transfer_status == highspy.HighsStatus.kError:
                raise _HessianTransferError(
                    "HiGHS rejected the quadratic objective Hessian."
                )

    try:
        with patch.object(
            Highs, "_set_objective", new=set_quadratic_objective
        ):
            Highs().solve(model)
    except _HessianTransferError:
        return {"objective": None, "status": "hessian_transfer_failed"}
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "infeasible_or_solver_failed"}
        raise

    try:
        obj_val = float(pyo.value(model.risk_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}