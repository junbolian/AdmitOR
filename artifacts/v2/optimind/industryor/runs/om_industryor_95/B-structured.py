# IR: {"sets":{"R":["A","B","D"],"P":["A","B"],"K":"pool-sulfur endpoints and real roots of basis determinants, feasibility-slack numerators, and stationary-profit numerators within the pool-sulfur interval"},"params":["sulfur_A","sulfur_B","sulfur_C","sulfur_D","price_A","price_B","price_C","price_D","sell_A","sell_B","max_sulfur_A","max_sulfur_B","supply_D","demand_A","demand_B"],"variables":{"weight[k]":"nonnegative continuous","raw[k,r]":"nonnegative continuous","pool[k,p]":"nonnegative continuous","direct_C[k,p]":"nonnegative continuous"},"constraints":["sum_k weight[k] = 1","sum_r raw[k,r] = sum_p pool[k,p] for each k","sum_r sulfur[r]*raw[k,r] = q[k]*sum_p pool[k,p] for each k","(q[k]-max_sulfur[p])*pool[k,p] + (sulfur[C]-max_sulfur[p])*direct_C[k,p] <= 0 for each k,p","pool[k,p]+direct_C[k,p] <= demand[p]*weight[k] for each k,p","raw[k,D] <= supply_D*weight[k] for each k"],"objective":"maximize sum_k(sum_p sell[p]*(pool[k,p]+direct_C[k,p])-sum_r price[r]*raw[k,r]-price[C]*sum_p direct_C[k,p])","method":"Enumerate globally sufficient pool-sulfur candidates using exact rational polynomial arithmetic from the Python standard library; solve the scaled convex hull of their fixed-concentration LPs with HiGHS. Its maximum objective equals the single-pool global maximum."}

from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    def rational(value):
        return Fraction(str(value))

    sulfur = {
        "A": rational(params["sulfur_A"]),
        "B": rational(params["sulfur_B"]),
        "C": rational(params["sulfur_C"]),
        "D": rational(params["sulfur_D"]),
    }
    price = {
        "A": rational(params["price_A"]),
        "B": rational(params["price_B"]),
        "C": rational(params["price_C"]),
        "D": rational(params["price_D"]),
    }
    sell = {
        "A": rational(params["sell_A"]),
        "B": rational(params["sell_B"]),
    }
    max_sulfur = {
        "A": rational(params["max_sulfur_A"]),
        "B": rational(params["max_sulfur_B"]),
    }
    supply_D = rational(params["supply_D"])
    demand = {
        "A": rational(params["demand_A"]),
        "B": rational(params["demand_B"]),
    }

    raw_types = ("A", "B", "D")
    products = ("A", "B")
    zero = Fraction(0)
    one = Fraction(1)

    # Polynomials are tuples of rational coefficients in ascending order.
    def trim(coefficients):
        result = list(coefficients)
        while len(result) > 1 and result[-1] == 0:
            result.pop()
        return tuple(result) if result else (zero,)

    def constant(value):
        return (Fraction(value),)

    def poly_add(left, right):
        result = [zero] * max(len(left), len(right))
        for position, coefficient in enumerate(left):
            result[position] += coefficient
        for position, coefficient in enumerate(right):
            result[position] += coefficient
        return trim(result)

    def poly_scale(polynomial, scalar):
        return trim([coefficient * scalar for coefficient in polynomial])

    def poly_sub(left, right):
        return poly_add(left, poly_scale(right, -one))

    def poly_mul(left, right):
        if left == (zero,) or right == (zero,):
            return (zero,)
        result = [zero] * (len(left) + len(right) - 1)
        for left_position, left_coefficient in enumerate(left):
            if left_coefficient == 0:
                continue
            for right_position, right_coefficient in enumerate(right):
                if right_coefficient != 0:
                    result[left_position + right_position] += (
                        left_coefficient * right_coefficient
                    )
        return trim(result)

    def poly_derivative(polynomial):
        return trim(
            [
                position * polynomial[position]
                for position in range(1, len(polynomial))
            ]
        )

    def poly_evaluate(polynomial, argument):
        result = zero
        for coefficient in reversed(polynomial):
            result = result * argument + coefficient
        return result

    def interpolate_quadratic(arguments, values):
        result = (zero,)
        for position in range(3):
            term = (one,)
            denominator = one
            for other_position in range(3):
                if position == other_position:
                    continue
                term = poly_mul(
                    term, (-arguments[other_position], one)
                )
                denominator *= (
                    arguments[position] - arguments[other_position]
                )
            result = poly_add(
                result,
                poly_scale(term, values[position] / denominator),
            )
        return result

    def determinant_and_solution(matrix, right_hand_side):
        """Return an exact determinant and solution, or None if singular."""
        dimension = len(matrix)
        work = [
            list(matrix[row_position]) + [right_hand_side[row_position]]
            for row_position in range(dimension)
        ]
        determinant = one

        for column_position in range(dimension):
            pivot_position = next(
                (
                    row_position
                    for row_position in range(column_position, dimension)
                    if work[row_position][column_position] != 0
                ),
                None,
            )
            if pivot_position is None:
                return None

            if pivot_position != column_position:
                work[column_position], work[pivot_position] = (
                    work[pivot_position],
                    work[column_position],
                )
                determinant = -determinant

            pivot = work[column_position][column_position]
            determinant *= pivot

            for row_position in range(column_position + 1, dimension):
                entry = work[row_position][column_position]
                if entry == 0:
                    continue
                multiplier = entry / pivot
                work[row_position][column_position] = zero
                for next_column in range(column_position + 1, dimension + 1):
                    work[row_position][next_column] -= (
                        multiplier * work[column_position][next_column]
                    )

        solution = [zero] * dimension
        for row_position in reversed(range(dimension)):
            residual = work[row_position][dimension] - sum(
                (
                    work[row_position][column_position]
                    * solution[column_position]
                    for column_position in range(row_position + 1, dimension)
                ),
                zero,
            )
            solution[row_position] = (
                residual / work[row_position][row_position]
            )

        return determinant, solution

    lower = min(sulfur[raw_type] for raw_type in raw_types)
    upper = max(sulfur[raw_type] for raw_type in raw_types)
    candidate_values = {float(lower), float(upper)}
    examined_polynomials = set()

    def decimal_fraction(value):
        return Decimal(value.numerator) / Decimal(value.denominator)

    def collect_roots(polynomial):
        polynomial = trim(polynomial)
        if len(polynomial) <= 1:
            return

        normalized = poly_scale(polynomial, one / polynomial[-1])
        if normalized in examined_polynomials:
            return
        examined_polynomials.add(normalized)

        degree = len(normalized) - 1
        if degree == 1:
            root = -normalized[0] / normalized[1]
            if lower <= root <= upper:
                candidate_values.add(float(root))
            return

        # Only the pool_A and pool_B columns depend on concentration.
        # Basis determinants, slack numerators, and profit-stationarity
        # numerators consequently have degree at most two.
        if degree != 2:
            raise ArithmeticError("Unexpected candidate polynomial degree.")

        coefficient_c, coefficient_b, coefficient_a = normalized
        discriminant = (
            coefficient_b * coefficient_b
            - 4 * coefficient_a * coefficient_c
        )
        if discriminant < 0:
            return

        with localcontext() as context:
            context.prec = 80
            lower_decimal = decimal_fraction(lower)
            upper_decimal = decimal_fraction(upper)
            coefficient_a_decimal = decimal_fraction(coefficient_a)
            coefficient_b_decimal = decimal_fraction(coefficient_b)
            coefficient_c_decimal = decimal_fraction(coefficient_c)

            if discriminant == 0:
                roots = (
                    -coefficient_b_decimal / (2 * coefficient_a_decimal),
                )
            else:
                square_root = decimal_fraction(discriminant).sqrt()
                signed_square_root = (
                    square_root
                    if coefficient_b_decimal >= 0
                    else -square_root
                )
                auxiliary = -(
                    coefficient_b_decimal + signed_square_root
                ) / 2
                roots = (
                    auxiliary / coefficient_a_decimal,
                    coefficient_c_decimal / auxiliary,
                )

            for root in roots:
                if lower_decimal <= root <= upper_decimal:
                    candidate_values.add(
                        min(float(upper), max(float(lower), float(root)))
                    )

    # Variable order for each fixed-concentration LP:
    # raw_A, raw_B, raw_D, pool_A, pool_B, direct_C_A, direct_C_B.
    equality_rows = [
        [
            constant(1), constant(1), constant(1),
            constant(-1), constant(-1), constant(0), constant(0),
        ],
        [
            constant(sulfur["A"]),
            constant(sulfur["B"]),
            constant(sulfur["D"]),
            (zero, -one),
            (zero, -one),
            constant(0),
            constant(0),
        ],
    ]

    inequality_rows = []
    inequality_bounds = []

    for variable_position in range(7):
        row = [constant(0) for _ in range(7)]
        row[variable_position] = constant(-1)
        inequality_rows.append(row)
        inequality_bounds.append(zero)

    inequality_rows.extend(
        [
            [
                constant(0), constant(0), constant(1),
                constant(0), constant(0), constant(0), constant(0),
            ],
            [
                constant(0), constant(0), constant(0),
                constant(1), constant(0), constant(1), constant(0),
            ],
            [
                constant(0), constant(0), constant(0),
                constant(0), constant(1), constant(0), constant(1),
            ],
            [
                constant(0), constant(0), constant(0),
                (-max_sulfur["A"], one),
                constant(0),
                constant(sulfur["C"] - max_sulfur["A"]),
                constant(0),
            ],
            [
                constant(0), constant(0), constant(0),
                constant(0),
                (-max_sulfur["B"], one),
                constant(0),
                constant(sulfur["C"] - max_sulfur["B"]),
            ],
        ]
    )
    inequality_bounds.extend(
        [supply_D, demand["A"], demand["B"], zero, zero]
    )

    profit_coefficients = [
        -price["A"],
        -price["B"],
        -price["D"],
        sell["A"],
        sell["B"],
        sell["A"] - price["C"],
        sell["B"] - price["C"],
    ]

    if lower != upper:
        # A nonzero quadratic determinant has at most two roots, so these
        # five distinct arguments provide three nonsingular evaluations.
        sample_arguments = [
            lower + (upper - lower) * Fraction(position, 4)
            for position in range(5)
        ]

        evaluated_equalities = [
            [
                [poly_evaluate(entry, argument) for entry in row]
                for row in equality_rows
            ]
            for argument in sample_arguments
        ]
        evaluated_inequalities = [
            [
                [poly_evaluate(entry, argument) for entry in row]
                for row in inequality_rows
            ]
            for argument in sample_arguments
        ]

        for active_positions in combinations(range(len(inequality_rows)), 5):
            right_hand_side = [zero, zero] + [
                inequality_bounds[position] for position in active_positions
            ]
            successful_arguments = []
            determinant_values = []
            numerator_values = [[] for _ in range(7)]
            singular_count = 0

            for sample_position, argument in enumerate(sample_arguments):
                matrix = evaluated_equalities[sample_position] + [
                    evaluated_inequalities[sample_position][position]
                    for position in active_positions
                ]
                result = determinant_and_solution(matrix, right_hand_side)

                if result is None:
                    singular_count += 1
                    if singular_count == 3:
                        break
                    continue

                determinant, solution = result
                successful_arguments.append(argument)
                determinant_values.append(determinant)
                for variable_position in range(7):
                    numerator_values[variable_position].append(
                        determinant * solution[variable_position]
                    )
                if len(successful_arguments) == 3:
                    break

            if len(successful_arguments) != 3:
                continue

            determinant_polynomial = interpolate_quadratic(
                successful_arguments, determinant_values
            )
            solution_numerators = [
                interpolate_quadratic(successful_arguments, values)
                for values in numerator_values
            ]

            collect_roots(determinant_polynomial)

            for row, bound in zip(inequality_rows, inequality_bounds):
                slack_numerator = poly_scale(
                    determinant_polynomial, bound
                )
                for coefficient, numerator in zip(row, solution_numerators):
                    slack_numerator = poly_sub(
                        slack_numerator, poly_mul(coefficient, numerator)
                    )
                collect_roots(slack_numerator)

            profit_numerator = (zero,)
            for coefficient, numerator in zip(
                profit_coefficients, solution_numerators
            ):
                profit_numerator = poly_add(
                    profit_numerator, poly_scale(numerator, coefficient)
                )

            stationary_numerator = poly_sub(
                poly_mul(
                    poly_derivative(profit_numerator),
                    determinant_polynomial,
                ),
                poly_mul(
                    profit_numerator,
                    poly_derivative(determinant_polynomial),
                ),
            )
            collect_roots(stationary_numerator)

    # Every fixed-concentration feasible region is bounded by product
    # demand. An optimum occurs at a vertex. Between the candidates above,
    # each basis has unchanged feasibility and a differentiable rational
    # profit function, whose interior extrema were included explicitly.
    concentrations = sorted(candidate_values)

    model = pyo.ConcreteModel()
    model.K = pyo.RangeSet(0, len(concentrations) - 1)
    model.R = pyo.Set(initialize=raw_types, ordered=True)
    model.P = pyo.Set(initialize=products, ordered=True)

    model.weight = pyo.Var(model.K, domain=pyo.NonNegativeReals)
    model.raw = pyo.Var(model.K, model.R, domain=pyo.NonNegativeReals)
    model.pool = pyo.Var(model.K, model.P, domain=pyo.NonNegativeReals)
    model.direct_C = pyo.Var(model.K, model.P, domain=pyo.NonNegativeReals)

    model.weight_total = pyo.Constraint(
        expr=sum(model.weight[k] for k in model.K) == 1
    )

    def tank_balance_rule(instance, k):
        return sum(
            instance.raw[k, raw_type] for raw_type in instance.R
        ) == sum(
            instance.pool[k, product] for product in instance.P
        )

    model.tank_balance = pyo.Constraint(model.K, rule=tank_balance_rule)

    def tank_sulfur_rule(instance, k):
        return sum(
            float(sulfur[raw_type]) * instance.raw[k, raw_type]
            for raw_type in instance.R
        ) == concentrations[k] * sum(
            instance.pool[k, product] for product in instance.P
        )

    model.tank_sulfur = pyo.Constraint(model.K, rule=tank_sulfur_rule)

    def product_quality_rule(instance, k, product):
        return (
            (concentrations[k] - float(max_sulfur[product]))
            * instance.pool[k, product]
            + float(sulfur["C"] - max_sulfur[product])
            * instance.direct_C[k, product]
            <= 0
        )

    model.product_quality = pyo.Constraint(
        model.K, model.P, rule=product_quality_rule
    )

    def market_limit_rule(instance, k, product):
        return (
            instance.pool[k, product] + instance.direct_C[k, product]
            <= float(demand[product]) * instance.weight[k]
        )

    model.market_limit = pyo.Constraint(
        model.K, model.P, rule=market_limit_rule
    )

    def raw_D_limit_rule(instance, k):
        return (
            instance.raw[k, "D"]
            <= float(supply_D) * instance.weight[k]
        )

    model.raw_D_limit = pyo.Constraint(model.K, rule=raw_D_limit_rule)

    # A linear objective has the same maximum over a union and its convex
    # hull. Thus this LP preserves the global single-tank optimal value.
    model.total_profit = pyo.Objective(
        expr=sum(
            sum(
                float(sell[product])
                * (model.pool[k, product] + model.direct_C[k, product])
                for product in model.P
            )
            - sum(
                float(price[raw_type]) * model.raw[k, raw_type]
                for raw_type in model.R
            )
            - float(price["C"])
            * sum(model.direct_C[k, product] for product in model.P)
            for k in model.K
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        message = str(exc).lower()
        if (
            "feasible solution was not found" in message
            or "no feasible solution" in message
            or "infeasible" in message
        ):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}