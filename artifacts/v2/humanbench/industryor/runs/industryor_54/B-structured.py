# IR: {"sets":{"categories":[1,2,3,4,5,6],"cities":["donghai","nanjiang"],"majors":[1,2,3],"competent":{"1":[1,2],"2":[2,3],"3":[1,3],"4":[1,3],"5":[2,3],"6":[3]},"preferred_major":{"1":1,"2":2,"3":1,"4":3,"5":3,"6":3},"preferred_city":{"1":"donghai","2":"donghai","3":"nanjiang","4":"nanjiang","5":"donghai","6":"nanjiang"}},"params":["demand_donghai_major1","demand_donghai_major2","demand_donghai_major3","demand_nanjiang_major1","demand_nanjiang_major2","demand_nanjiang_major3","category1_size","category2_size","category3_size","category4_size","category5_size","category6_size","preferred_major_goal","preferred_city_goal"],"variables":{"x[category,city,competent_major]":"nonnegative integer","demand_shortfall[city,major]":"nonnegative real","demand_excess[city,major]":"nonnegative real","major_shortfall":"nonnegative real","city_shortfall":"nonnegative real"},"constraints":["For each category: sum of its assignments <= category_size.","For each city and major: assignments + demand_shortfall - demand_excess = demand.","Preferred-major assignments + major_shortfall >= preferred_major_goal.","Preferred-city assignments + city_shortfall >= preferred_city_goal.","After optimizing each nonfinal priority, fix its objective expression to its attained optimum."],"objective":{"sense":"minimize","method":"sequential lexicographic","priorities":["sum(demand_shortfall + demand_excess)","major_shortfall","city_shortfall"],"reported_objective":"final-priority city_shortfall after fixing the first two optima"}}
import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    categories = (1, 2, 3, 4, 5, 6)
    cities = ("donghai", "nanjiang")
    majors = (1, 2, 3)

    demand = {
        ("donghai", 1): params["demand_donghai_major1"],
        ("donghai", 2): params["demand_donghai_major2"],
        ("donghai", 3): params["demand_donghai_major3"],
        ("nanjiang", 1): params["demand_nanjiang_major1"],
        ("nanjiang", 2): params["demand_nanjiang_major2"],
        ("nanjiang", 3): params["demand_nanjiang_major3"],
    }
    category_size = {
        1: params["category1_size"],
        2: params["category2_size"],
        3: params["category3_size"],
        4: params["category4_size"],
        5: params["category5_size"],
        6: params["category6_size"],
    }
    preferred_major_goal = params["preferred_major_goal"]
    preferred_city_goal = params["preferred_city_goal"]

    competent = {
        1: (1, 2),
        2: (2, 3),
        3: (1, 3),
        4: (1, 3),
        5: (2, 3),
        6: (3,),
    }
    preferred_major = {1: 1, 2: 2, 3: 1, 4: 3, 5: 3, 6: 3}
    preferred_city = {
        1: "donghai",
        2: "donghai",
        3: "nanjiang",
        4: "nanjiang",
        5: "donghai",
        6: "nanjiang",
    }

    assignment_keys = [
        (category, city, major)
        for category in categories
        for city in cities
        for major in competent[category]
    ]

    model = pyo.ConcreteModel()
    model.categories = pyo.Set(initialize=categories, ordered=True)
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.majors = pyo.Set(initialize=majors, ordered=True)
    model.assignment_keys = pyo.Set(
        dimen=3, initialize=assignment_keys, ordered=True
    )

    model.x = pyo.Var(model.assignment_keys, domain=pyo.NonNegativeIntegers)
    model.demand_shortfall = pyo.Var(
        model.cities, model.majors, domain=pyo.NonNegativeReals
    )
    model.demand_excess = pyo.Var(
        model.cities, model.majors, domain=pyo.NonNegativeReals
    )
    model.major_shortfall = pyo.Var(domain=pyo.NonNegativeReals)
    model.city_shortfall = pyo.Var(domain=pyo.NonNegativeReals)

    def category_capacity_rule(model, category):
        return (
            sum(
                model.x[category, city, major]
                for city in cities
                for major in competent[category]
            )
            <= category_size[category]
        )

    model.category_capacity = pyo.Constraint(
        model.categories, rule=category_capacity_rule
    )

    def demand_balance_rule(model, city, major):
        return (
            sum(
                model.x[category, city, major]
                for category in categories
                if major in competent[category]
            )
            + model.demand_shortfall[city, major]
            - model.demand_excess[city, major]
            == demand[city, major]
        )

    model.demand_balance = pyo.Constraint(
        model.cities, model.majors, rule=demand_balance_rule
    )

    model.preferred_major_requirement = pyo.Constraint(
        expr=(
            sum(
                model.x[category, city, preferred_major[category]]
                for category in categories
                for city in cities
            )
            + model.major_shortfall
            >= preferred_major_goal
        )
    )

    model.preferred_city_requirement = pyo.Constraint(
        expr=(
            sum(
                model.x[category, preferred_city[category], major]
                for category in categories
                for major in competent[category]
            )
            + model.city_shortfall
            >= preferred_city_goal
        )
    )

    model.first_priority = pyo.Expression(
        expr=sum(
            model.demand_shortfall[city, major]
            + model.demand_excess[city, major]
            for city in cities
            for major in majors
        )
    )
    model.second_priority = pyo.Expression(expr=model.major_shortfall)
    model.third_priority = pyo.Expression(expr=model.city_shortfall)

    model.priority_locks = pyo.ConstraintList()
    model.goal_objective = pyo.Objective(
        expr=model.first_priority, sense=pyo.minimize
    )

    priorities = (
        model.first_priority,
        model.second_priority,
        model.third_priority,
    )

    for priority_position, priority_expression in enumerate(priorities):
        model.goal_objective.set_value(priority_expression)

        # Only solver execution and objective retrieval are guarded.
        try:
            Highs().solve(model)
        except (RuntimeError, ApplicationError):
            return {"objective": None, "status": "solver_failed"}

        try:
            obj_val = float(pyo.value(model.goal_objective))
        except (ValueError, TypeError):
            return {"objective": None, "status": "objective_unavailable"}

        if priority_position < len(priorities) - 1:
            model.priority_locks.add(priority_expression == obj_val)

    return {"objective": obj_val, "status": "optimal"}