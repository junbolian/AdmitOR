# panel_base_2of3 label misses that are not panel_base_3of3 label misses

Included: the problems of Table 2b on the OptMATH sets, ruler `round_aware` (scripts/score_eval.py): panel_base_2of3 certifies them with a value that differs from the label and panel_base_3of3 does not certify them. Section 2 gives the families of the certifying clique and the value each family returns at instance 0. Problem text is the `question` field given to the models; objective values are from `verdict_full.json` (param_screen) and `verdict_independent.json` (independent). Classes are in artifacts/v2/audit.

| Sample id | Set | panel_base_2of3 value | Label | Rules that certify it | Certifying clique (families agreeing at instance 0) |
|---|---|---|---|---|---|
| `sample_11` | stream (OptMATH-295) | 10510918.0 | 10622791.791367784 | gate, panel_base_2of3, ind_gate | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| `sample_45` | stream (OptMATH-295) | 40911.0 | 41877.5 | gate, panel_base_2of3, ind_gate | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| `sample_58` | stream (OptMATH-295) | 2361.0 | 41673.0 | gate, panel_base_2of3, ind_gate | A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5) |
| `sample_65` | stream (OptMATH-295) | 780930.0 | 772406.0 | gate, panel_base_2of3, ind_gate | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| `sample_77` | stream (OptMATH-295) | 17994.0 | 17514.0 | gate, panel_base_2of3, ind_gate | A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5) |
| `sample_147` | stream (OptMATH-295) | 2927.0 | 3140.0 | gate, panel_base_2of3, ind_gate | A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5) |
| `sample_200` | stream (OptMATH-295) | 2.0 | 4.0 | panel_base_2of3 | A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5) |
| `sample_220` | stream (OptMATH-295) | 28057.684210526317 | 27737.0 | panel_base_2of3 | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| `sample_243` | stream (OptMATH-295) | 0.013513534831648254 | 0.012070001450990001 | gate, panel_base_2of3, ind_gate | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| `sample_290` | stream (OptMATH-295) | 811608.0 | 800200.0 | gate, panel_base_2of3, ind_gate | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol) |
| `conf_16675` | confirm (OptMATH-200) | 1235.5699207670264 | 2347.1979356914976 | gate, panel_base_2of3, ind_gate | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| `conf_66014` | confirm (OptMATH-200) | 11250495.529411767 | 11417460.619134724 | gate, panel_base_2of3, ind_gate | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| `conf_120613` | confirm (OptMATH-200) | 1844.0 | 1819.0 | gate, panel_base_2of3, ind_gate | A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5) |

## 1. sample_11 (stream (OptMATH-295))

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `sample_11` |
| Set | stream (OptMATH-295) |
| Source record | OptMATH-Train record 177392 |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 10510918.0 |
| Label | 10622791.791367784 |
| Rules that certify it | gate, panel_base_2of3, ind_gate (values: 10510918.0) |
| Label source | `artifacts/v2/optmath_295/problems.csv`, OptMATH-Train record 177392, field `answer`; the dataset stores no solution |

### 2. Certifying clique of panel_base_2of3 and values at instance 0

Families that agree at the stated instance (abs(a-b) <= 1e-4*max(1,|a|,|b|)): B (GPT-6.1 Sol) and C (Claude Sonnet 5.5). The third family: A (DeepSeek-V4-Flash) returns none.

| Family | Program | Value at instance 0 | Status at instance 0 | In the certifying clique | Matches the label (round_aware) |
|---|---|---|---|---|---|
| A (DeepSeek-V4-Flash) | A-direct.py | none | infeasible_or_unbounded | no | no |
| B (GPT-6.1 Sol) | B-structured.py | 10510918.0 | optimal | yes | no |
| C (Claude Sonnet 5.5) | C-direct.py | 10510918.0 | optimal | yes | no |

### 3. Problem text

```
You are managing a production facility that manufactures 45 different types of items. Each item has a specific profit margin associated with it, and your goal is to maximize the total profit from production while adhering to resource constraints and production limits.

#### Key Details:
1. **Profit Margins**: Each item generates a specific profit per unit produced. For example:
   - Item 0 yields a profit of 381 units per unit produced.
   - Item 1 yields 336 units, Item 2 yields 352 units, and so on, up to Item 44, which yields 381 units.

2. **Resource Constraint**: The production process relies on a critical resource that is limited to 404 units. Each item consumes a specific fraction of this resource per unit produced. For instance:
   - Producing one unit of Item 0 consumes 0.012048 units of the resource.
   - Producing one unit of Item 1 consumes 0.012821 units, and so on, up to Item 44, which consumes 0.012821 units per unit produced.
   - The total resource consumption across all items must not exceed 404 units.

3. **Production Limits**: Each item has a maximum production capacity due to operational constraints. For example:
   - Item 0 can be produced up to 716 units.
   - Item 1 can be produced up to 606 units, Item 2 up to 635 units, and so on, up to Item 44, which can be produced up to 618 units.
   - Additionally, production quantities cannot be negative; they must be zero or greater.

#### Objective:
Your task is to determine the optimal production quantity for each item to maximize total profit while ensuring that:
- The total resource consumption does not exceed 404 units.
- The production quantity for each item stays within its specified upper limit.
- All production quantities are non-negative.

#### Example:
- If you produce 100 units of Item 0, it would consume 1.2048 units of the resource and contribute 38,100 units to the total profit.
- If you produce 200 units of Item 1, it would consume 2.5642 units of the resource and contribute 67,200 units to the total profit.

By carefully balancing production quantities across all items, you aim to achieve the highest possible profit without violating any constraints.
```

### 4. spec.json (`spec` and `warnings`)

```json
"profit_margins": {"base":[381,336,352,381,336,352,381,336,352,381,336,352,381,336,352,381,336,352,381,336,352,381,336,352,381,336,352,381,336,352,381,336,352,381,336,352,381,336,352,381,336,352,381,336,381],"perturb":{"mode":"rel","r":0.5}}
"resource_coefficients": {"base":[0.012048,0.012821,0.012821,0.012048,0.012821,0.012821,0.012048,0.012821,0.012821,0.012048,0.012821,0.012821,0.012048,0.012821,0.012821,0.012048,0.012821,0.012821,0.012048,0.012821,0.012821,0.012048,0.012821,0.012821,0.012048,0.012821,0.012821,0.012048,0.012821,0.012821,0.012048,0.012821,0.012821,0.012048,0.012821,0.012821,0.012048,0.012821,0.012821,0.012048,0.012821,0.012821,0.012048,0.012821,0.012821],"perturb":{"mode":"rel","r":0.5}}
"resource_capacity": {"base":404,"perturb":{"mode":"rel","r":0.5}}
"production_capacities": {"base":[716,606,635,716,606,635,716,606,635,716,606,635,716,606,635,716,606,635,716,606,635,716,606,635,716,606,635,716,606,635,716,606,635,716,606,635,716,606,635,716,606,635,716,606,618],"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

### 5. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_margins = params["profit_margins"]
    resource_coefficients = params["resource_coefficients"]
    resource_capacity = params["resource_capacity"]
    production_capacities = params["production_capacities"]

    item_indices = list(range(len(profit_margins)))

    model = pyo.ConcreteModel()
    model.item_set = pyo.Set(initialize=item_indices)

    model.quantity = pyo.Var(model.item_set, within=pyo.NonNegativeReals)

    def quantity_bounds_rule(m, i):
        return (0, production_capacities[i])
    model.quantity_bounds = pyo.Constraint(model.item_set, rule=quantity_bounds_rule)

    def resource_rule(m):
        return sum(resource_coefficients[i] * m.quantity[i] for i in m.item_set) <= resource_capacity
    model.resource_constraint = pyo.Constraint(rule=resource_rule)

    def objective_rule(m):
        return sum(profit_margins[i] * m.quantity[i] for i in m.item_set)
    model.profit_objective = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit_objective))
    return {'objective': obj_val, 'status': 'optimal'}
```

#### B-structured.py

```python
# IR: {"sets":{"I":"0..44"},"params":{"profit_margins":"real[I]","resource_coefficients":"real[I]","resource_capacity":"real","production_capacities":"real[I]"},"variables":{"production":{"type":"continuous","domain":"nonnegative","index":"I"}},"constraints":["sum(resource_coefficients[i]*production[i] for i in I) <= resource_capacity","production[i] <= production_capacities[i] for i in I"],"objective":{"sense":"maximize","expression":"sum(profit_margins[i]*production[i] for i in I)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_margins = params["profit_margins"]
    resource_coefficients = params["resource_coefficients"]
    resource_capacity = params["resource_capacity"]
    production_capacities = params["production_capacities"]

    model = pyo.ConcreteModel()
    model.item_indices = pyo.RangeSet(0, 44)

    model.profit_margins = pyo.Param(
        model.item_indices,
        initialize={i: profit_margins[i] for i in model.item_indices},
        within=pyo.Reals,
    )
    model.resource_coefficients = pyo.Param(
        model.item_indices,
        initialize={i: resource_coefficients[i] for i in model.item_indices},
        within=pyo.Reals,
    )
    model.resource_capacity = pyo.Param(
        initialize=resource_capacity,
        within=pyo.Reals,
    )
    model.production_capacities = pyo.Param(
        model.item_indices,
        initialize={i: production_capacities[i] for i in model.item_indices},
        within=pyo.Reals,
    )

    model.production = pyo.Var(
        model.item_indices,
        domain=pyo.NonNegativeReals,
    )

    model.resource_limit = pyo.Constraint(
        expr=sum(
            model.resource_coefficients[i] * model.production[i]
            for i in model.item_indices
        )
        <= model.resource_capacity
    )

    def production_limit_rule(instance, i):
        return instance.production[i] <= instance.production_capacities[i]

    model.production_limits = pyo.Constraint(
        model.item_indices,
        rule=production_limit_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_margins[i] * model.production[i]
            for i in model.item_indices
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB


def solve(params):
    profit_margins = params["profit_margins"]
    resource_coefficients = params["resource_coefficients"]
    resource_capacity = params["resource_capacity"]
    production_capacities = params["production_capacities"]

    n = len(profit_margins)
    upper_bounds = [float(v) for v in production_capacities]

    model = gp.Model("production")
    model.Params.OutputFlag = 0

    x = model.addVars(n, lb=0.0, ub=upper_bounds, name="x")

    model.setObjective(
        gp.quicksum(float(profit_margins[i]) * x[i] for i in range(n)),
        GRB.MAXIMIZE,
    )

    model.addConstr(
        gp.quicksum(float(resource_coefficients[i]) * x[i] for i in range(n))
        <= float(resource_capacity),
        name="resource",
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.Status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "inf_or_unbounded"}
    if model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}

    return {"objective": None, "status": f"status_{model.Status}"}
```

### 6. Objective values

Rules that certify it: gate, panel_base_2of3, ind_gate.

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (infeasible_or_unbounded) | 10510918.0 (optimal) | 10510918.0 (optimal) |
| 1 | none (infeasible_or_unbounded) | 8627646.853865175 (optimal) | 8627646.853865178 (optimal) |
| 2 | none (infeasible_or_unbounded) | 10229268.09245582 (optimal) | 10229268.092455823 (optimal) |
| 3 | none (infeasible_or_unbounded) | 9959881.84149111 (optimal) | 9959881.841491109 (optimal) |
| 4 | none (infeasible_or_unbounded) | 10487329.422530897 (optimal) | 10487329.422530899 (optimal) |
| 5 | none (infeasible_or_unbounded) | 9632022.05193519 (optimal) | 9632022.051935196 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (infeasible_or_unbounded) | 10510918.0 (optimal) | 10510918.0 (optimal) |
| 1 | none (infeasible_or_unbounded) | 8627646.853865175 (optimal) | 8627646.853865178 (optimal) |
| 2 | none (infeasible_or_unbounded) | 10229268.09245582 (optimal) | 10229268.092455823 (optimal) |
| 3 | none (infeasible_or_unbounded) | 9959881.84149111 (optimal) | 9959881.841491109 (optimal) |
| 4 | none (infeasible_or_unbounded) | 10487329.422530897 (optimal) | 10487329.422530899 (optimal) |
| 5 | none (infeasible_or_unbounded) | 9632022.05193519 (optimal) | 9632022.051935196 (optimal) |


## 2. sample_45 (stream (OptMATH-295))

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `sample_45` |
| Set | stream (OptMATH-295) |
| Source record | OptMATH-Train record 200145 |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 40911.0 |
| Label | 41877.5 |
| Rules that certify it | gate, panel_base_2of3, ind_gate (values: 40911.0) |
| Label source | `artifacts/v2/optmath_295/problems.csv`, OptMATH-Train record 200145, field `answer`; the dataset stores no solution |

### 2. Certifying clique of panel_base_2of3 and values at instance 0

Families that agree at the stated instance (abs(a-b) <= 1e-4*max(1,|a|,|b|)): B (GPT-6.1 Sol) and C (Claude Sonnet 5.5). The third family: A (DeepSeek-V4-Flash) returns 42125.5.

| Family | Program | Value at instance 0 | Status at instance 0 | In the certifying clique | Matches the label (round_aware) |
|---|---|---|---|---|---|
| A (DeepSeek-V4-Flash) | A-direct.py | 42125.5 | optimal | no | no |
| B (GPT-6.1 Sol) | B-structured.py | 40911.0 | optimal | yes | no |
| C (Claude Sonnet 5.5) | C-direct.py | 40911.0 | optimal | yes | no |

### 3. Problem text

```
You are tasked with managing the production, inventory, and sales of three products (product_0, product_1, and product_2) over a four-period planning horizon. The goal is to maximize the total profit while adhering to production capacity, inventory limits, and sales constraints. Here’s the detailed scenario:

#### **Objective:**
Maximize the total profit, which is calculated as the revenue from sales minus the cost of holding inventory. The profit per unit sold for each product is as follows:
- Product_0: \$106 per unit
- Product_1: \$151 per unit
- Product_2: \$143 per unit

The holding cost for inventory is \$10 per unit per period, regardless of the product.

#### **Decisions to Make:**
1. **Production:** Determine how many units of each product to manufacture in each period.
2. **Inventory:** Decide how many units of each product to store at the end of each period.
3. **Sales:** Determine how many units of each product to sell in each period.

#### **Constraints and Conditions:**

1. **Initial Balance (Period 0):**
   - The production of each product in the first period must equal the sum of its sales and inventory for that period. For example:
     - For product_0: Production[0,product_0] = Sales[0,product_0] + Inventory[0,product_0].
     - Similar constraints apply to product_1 and product_2.

2. **Inventory Balance (Periods 1 to 3):**
   - For each subsequent period, the inventory carried over from the previous period plus the production in the current period must equal the sum of sales and inventory for that period. For example:
     - For product_0 in period 1: Production[1,product_0] + Inventory[0,product_0] = Sales[1,product_0] + Inventory[1,product_0].
     - This balance must be maintained for all products and periods.

3. **Production Capacity:**
   - The factory has three types of machines: grinders, drills, and borers. Each machine type has a limited capacity per period, and some machines may be down for maintenance, reducing available capacity. The production of each product consumes machine time as follows:
     - Grinders: Each unit of product_0, product_1, and product_2 requires 2 hours on a grinder.
     - Drills: Each unit of product_0 requires 2 hours, while product_1 and product_2 require 1 hour each.
     - Borers: Each unit of product_0 and product_1 requires 2 hours, while product_2 requires 1 hour.
   - The total machine hours used in each period cannot exceed the available capacity:
     - Grinders: 240 hours in periods 0 and 2, 120 hours in periods 1 and 3.
     - Drills: 120 hours in all periods.
     - Borers: 120 hours in all periods.

4. **Inventory Limits:**
   - The maximum inventory capacity for each product in any period is 50 units. For example:
     - Inventory[0,product_0] ≤ 50, Inventory[1,product_1] ≤ 50, and so on for all products and periods.

5. **Sales Limits:**
   - The maximum number of units that can be sold for each product in each period is as follows:
     - Period 0: product_0 ≤ 44, product_1 ≤ 46, product_2 ≤ 27.
     - Period 1: product_0 ≤ 42, product_1 ≤ 34, product_2 ≤ 37.
     - Period 2: product_0 ≤ 24, product_1 ≤ 50, product_2 ≤ 48.
     - Period 3: product_0 ≤ 42, product_1 ≤ 29, product_2 ≤ 43.

6. **Target Inventory:**
   - At the end of the planning horizon (period 3), the inventory for each product must meet a target level of 10 units. For example:
     - Inventory[3,product_0] = 10, Inventory[3,product_1] = 10, Inventory[3,product_2] = 10.

7. **Non-Negativity:**
   - Production, inventory, and sales quantities must be non-negative for all products and periods.

#### **Summary:**
Your task is to determine the optimal production, inventory, and sales quantities for each product in each period to maximize profit, while ensuring that production does not exceed machine capacities, inventory stays within limits, sales do not surpass demand, and target inventory levels are met at the end of the planning horizon.
```

### 4. spec.json (`spec` and `warnings`)

```json
"profit_per_unit": {"base":[106,151,143],"perturb":{"mode":"rel","r":0.35}}
"holding_cost": {"base":10,"perturb":{"mode":"abs","lo":0.0,"hi":30.0,"integer":false}}
"machine_hours_per_unit": {"base":[[2,2,2],[2,1,2],[2,1,1]],"perturb":{"mode":"rel","r":0.25}}
"grinder_capacity": {"base":[240,120,240,120],"perturb":{"mode":"rel","r":0.4}}
"drill_capacity": {"base":[120,120,120,120],"perturb":{"mode":"rel","r":0.4}}
"borer_capacity": {"base":[120,120,120,120],"perturb":{"mode":"rel","r":0.4}}
"inventory_capacity": {"base":50,"perturb":{"mode":"abs","lo":25.0,"hi":80.0,"integer":true}}
"sales_limit": {"base":[[44,46,27],[42,34,37],[24,50,48],[42,29,43]],"perturb":{"mode":"rel","r":0.3}}
"target_inventory": {"base":[10,10,10],"perturb":{"mode":"abs","lo":0.0,"hi":25.0,"integer":true}}
```

Warnings:

```
none
```

### 5. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    machine_hours_per_unit = params["machine_hours_per_unit"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    inventory_capacity = params["inventory_capacity"]
    sales_limit = params["sales_limit"]
    target_inventory = params["target_inventory"]

    periods = list(range(4))
    products = list(range(3))
    machines = ["grinder", "drill", "borer"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=periods)
    model.J = pyo.Set(initialize=products)

    model.prod = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            profit_per_unit[j] * m.sales[t, j] for t in m.P for j in m.J
        ) - sum(
            holding_cost * m.inv[t, j] for t in m.P for j in m.J
        )

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def balance_p0(m, j):
        return m.prod[0, j] == m.sales[0, j] + m.inv[0, j]

    model.balance_p0 = pyo.Constraint(model.J, rule=balance_p0)

    def balance_mid(m, t, j):
        return m.inv[t - 1, j] + m.prod[t, j] == m.sales[t, j] + m.inv[t, j]

    model.balance_mid = pyo.Constraint(
        [t for t in periods if t >= 1], model.J, rule=balance_mid
    )

    def grind_cap(m, t):
        return (
            machine_hours_per_unit[0][0] * m.prod[t, 0]
            + machine_hours_per_unit[0][1] * m.prod[t, 1]
            + machine_hours_per_unit[0][2] * m.prod[t, 2]
            <= grinder_capacity[t]
        )

    model.grind_cap = pyo.Constraint(model.P, rule=grind_cap)

    def drill_cap(m, t):
        return (
            machine_hours_per_unit[1][0] * m.prod[t, 0]
            + machine_hours_per_unit[1][1] * m.prod[t, 1]
            + machine_hours_per_unit[1][2] * m.prod[t, 2]
            <= drill_capacity[t]
        )

    model.drill_cap = pyo.Constraint(model.P, rule=drill_cap)

    def borer_cap(m, t):
        return (
            machine_hours_per_unit[2][0] * m.prod[t, 0]
            + machine_hours_per_unit[2][1] * m.prod[t, 1]
            + machine_hours_per_unit[2][2] * m.prod[t, 2]
            <= borer_capacity[t]
        )

    model.borer_cap = pyo.Constraint(model.P, rule=borer_cap)

    def inv_limit(m, t, j):
        return m.inv[t, j] <= inventory_capacity

    model.inv_limit = pyo.Constraint(model.P, model.J, rule=inv_limit)

    def sales_lim(m, t, j):
        return m.sales[t, j] <= sales_limit[t][j]

    model.sales_lim = pyo.Constraint(model.P, model.J, rule=sales_lim)

    def target_rule(m, j):
        return m.inv[3, j] == target_inventory[j]

    model.target_rule = pyo.Constraint(model.J, rule=target_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"T":[0,1,2,3],"P":[0,1,2],"K":[0,1,2]},"params":{"profit_per_unit":"P-indexed","holding_cost":"scalar","machine_hours_per_unit":"P-by-K; K=grinder,drill,borer","grinder_capacity":"T-indexed","drill_capacity":"T-indexed","borer_capacity":"T-indexed","inventory_capacity":"scalar or P-indexed","sales_limit":"T-by-P","target_inventory":"scalar or P-indexed"},"variables":{"production[T,P]":"nonnegative continuous","inventory[T,P]":"nonnegative continuous","sales[T,P]":"nonnegative continuous"},"constraints":["production[0,p]=sales[0,p]+inventory[0,p] for p in P","production[t,p]+inventory[t-1,p]=sales[t,p]+inventory[t,p] for t in T excluding 0,p in P","sum(machine_hours_per_unit[p,k]*production[t,p] for p in P)<=machine_capacity[k,t] for k in K,t in T; machine_capacity comes from grinder_capacity,drill_capacity,borer_capacity","inventory[t,p]<=inventory_capacity[p] for t in T,p in P; broadcast scalar capacity","sales[t,p]<=sales_limit[t,p] for t in T,p in P","inventory[3,p]=target_inventory[p] for p in P; broadcast scalar target"],"objective":"maximize sum(profit_per_unit[p]*sales[t,p]-holding_cost*inventory[t,p] for t in T,p in P)"}

from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the continuous production, inventory, and sales planning model."""

    profit_data = params["profit_per_unit"]
    holding_data = params["holding_cost"]
    hours_data = params["machine_hours_per_unit"]
    grinder_data = params["grinder_capacity"]
    drill_data = params["drill_capacity"]
    borer_data = params["borer_capacity"]
    inventory_data = params["inventory_capacity"]
    sales_data = params["sales_limit"]
    target_data = params["target_inventory"]

    def product_value(data, product):
        return data if isinstance(data, Number) else data[product]

    capacity_data = (grinder_data, drill_data, borer_data)

    model = pyo.ConcreteModel()

    model.periods = pyo.RangeSet(0, 3)
    model.products = pyo.RangeSet(0, 2)
    model.machine_types = pyo.RangeSet(0, 2)

    model.unit_profit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: profit_data[product],
    )
    model.unit_holding_cost = pyo.Param(initialize=holding_data)
    model.machine_hours = pyo.Param(
        model.products,
        model.machine_types,
        initialize=lambda mdl, product, machine: hours_data[product][machine],
    )
    model.machine_capacity = pyo.Param(
        model.machine_types,
        model.periods,
        initialize=lambda mdl, machine, period: capacity_data[machine][period],
    )
    model.inventory_limit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: product_value(inventory_data, product),
    )
    model.sales_limit = pyo.Param(
        model.periods,
        model.products,
        initialize=lambda mdl, period, product: sales_data[period][product],
    )
    model.final_inventory_target = pyo.Param(
        model.products,
        initialize=lambda mdl, product: product_value(target_data, product),
    )

    model.production = pyo.Var(
        model.periods, model.products, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.periods, model.products, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
        model.periods, model.products, domain=pyo.NonNegativeReals
    )

    def initial_balance_rule(mdl, product):
        return (
            mdl.production[0, product]
            == mdl.sales[0, product] + mdl.inventory[0, product]
        )

    model.initial_balance = pyo.Constraint(
        model.products, rule=initial_balance_rule
    )

    def inventory_balance_rule(mdl, period, product):
        if period == 0:
            return pyo.Constraint.Skip
        return (
            mdl.production[period, product] + mdl.inventory[period - 1, product]
            == mdl.sales[period, product] + mdl.inventory[period, product]
        )

    model.inventory_balance = pyo.Constraint(
        model.periods, model.products, rule=inventory_balance_rule
    )

    def machine_capacity_rule(mdl, machine, period):
        return (
            sum(
                mdl.machine_hours[product, machine]
                * mdl.production[period, product]
                for product in mdl.products
            )
            <= mdl.machine_capacity[machine, period]
        )

    model.machine_capacity_constraints = pyo.Constraint(
        model.machine_types, model.periods, rule=machine_capacity_rule
    )

    model.inventory_capacity_constraints = pyo.Constraint(
        model.periods,
        model.products,
        rule=lambda mdl, period, product: (
            mdl.inventory[period, product] <= mdl.inventory_limit[product]
        ),
    )

    model.sales_limit_constraints = pyo.Constraint(
        model.periods,
        model.products,
        rule=lambda mdl, period, product: (
            mdl.sales[period, product] <= mdl.sales_limit[period, product]
        ),
    )

    model.final_inventory_constraints = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.inventory[3, product] == mdl.final_inventory_target[product]
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[product] * model.sales[period, product]
            - model.unit_holding_cost * model.inventory[period, product]
            for period in model.periods
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    machine_hours_per_unit = params["machine_hours_per_unit"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    inventory_capacity = params["inventory_capacity"]
    sales_limit = params["sales_limit"]
    target_inventory = params["target_inventory"]

    n_products = 3
    n_periods = 4
    machine_caps = [grinder_capacity, drill_capacity, borer_capacity]

    if isinstance(inventory_capacity, (int, float)):
        inv_cap = [inventory_capacity] * n_products
    else:
        inv_cap = list(inventory_capacity)

    model = gp.Model("production_planning")
    model.Params.OutputFlag = 0

    prod = {}
    inv = {}
    sales = {}
    for t in range(n_periods):
        for p in range(n_products):
            prod[t, p] = model.addVar(lb=0, name=f"prod_{t}_{p}")
            inv[t, p] = model.addVar(lb=0, name=f"inv_{t}_{p}")
            sales[t, p] = model.addVar(lb=0, name=f"sales_{t}_{p}")
    model.update()

    obj = gp.LinExpr()
    for t in range(n_periods):
        for p in range(n_products):
            obj += profit_per_unit[p] * sales[t, p]
            obj -= holding_cost * inv[t, p]
    model.setObjective(obj, GRB.MAXIMIZE)

    for p in range(n_products):
        model.addConstr(prod[0, p] == sales[0, p] + inv[0, p])
        for t in range(1, n_periods):
            model.addConstr(prod[t, p] + inv[t - 1, p] == sales[t, p] + inv[t, p])

    for t in range(n_periods):
        for m_idx in range(3):
            cap = machine_caps[m_idx][t]
            expr = gp.LinExpr()
            for p in range(n_products):
                expr += machine_hours_per_unit[p][m_idx] * prod[t, p]
            model.addConstr(expr <= cap)

    for t in range(n_periods):
        for p in range(n_products):
            model.addConstr(inv[t, p] <= inv_cap[p])

    for t in range(n_periods):
        for p in range(n_products):
            model.addConstr(sales[t, p] <= sales_limit[t][p])

    for p in range(n_products):
        model.addConstr(inv[n_periods - 1, p] == target_inventory[p])

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": "failed"}
```

### 6. Objective values

Rules that certify it: gate, panel_base_2of3, ind_gate.

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 42125.5 (optimal) | 40911.0 (optimal) | 40911.0 (optimal) |
| 1 | 21946.744222089997 (optimal) | 28155.017290387554 (optimal) | 28155.017290387557 (optimal) |
| 2 | 37803.91895575223 (optimal) | 35471.18073765622 (optimal) | 35471.18073765622 (optimal) |
| 3 | 53228.85154718077 (optimal) | 41312.05226899813 (optimal) | 41312.05226899813 (optimal) |
| 4 | 24037.656207459244 (optimal) | 25847.18499600206 (optimal) | 25847.184996002063 (optimal) |
| 5 | 28808.92242243085 (optimal) | 31334.673423570814 (optimal) | 31334.67342357082 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 42125.5 (optimal) | 40911.0 (optimal) | 40911.0 (optimal) |
| 1 | 21946.744222089997 (optimal) | 28155.017290387554 (optimal) | 28155.017290387557 (optimal) |
| 2 | 37803.91895575223 (optimal) | 35471.18073765622 (optimal) | 35471.18073765622 (optimal) |
| 3 | 53228.85154718077 (optimal) | 41312.05226899813 (optimal) | 41312.05226899813 (optimal) |
| 4 | 24037.656207459244 (optimal) | 25847.18499600206 (optimal) | 25847.184996002063 (optimal) |
| 5 | 28808.92242243085 (optimal) | 31334.673423570814 (optimal) | 31334.67342357082 (optimal) |


## 3. sample_58 (stream (OptMATH-295))

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `sample_58` |
| Set | stream (OptMATH-295) |
| Source record | OptMATH-Train record 140568 |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 2361.0 |
| Label | 41673.0 |
| Rules that certify it | gate, panel_base_2of3, ind_gate (values: 2361.0) |
| Label source | `artifacts/v2/optmath_295/problems.csv`, OptMATH-Train record 140568, field `answer`; the dataset stores no solution |

### 2. Certifying clique of panel_base_2of3 and values at instance 0

Families that agree at the stated instance (abs(a-b) <= 1e-4*max(1,|a|,|b|)): A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5). The third family: B (GPT-6.1 Sol) returns none.

| Family | Program | Value at instance 0 | Status at instance 0 | In the certifying clique | Matches the label (round_aware) |
|---|---|---|---|---|---|
| A (DeepSeek-V4-Flash) | A-direct.py | 2361.0 | optimal | yes | no |
| B (GPT-6.1 Sol) | B-structured.py | none | crash:initialize=lambda mdl, i: params["values"][i], \| ~~~~~~~~~~~~~~~~^^^ \| IndexError: list index out of range | no | no |
| C (Claude Sonnet 5.5) | C-direct.py | 2361.0 | optimal | yes | no |

### 3. Problem text

```
You are tasked with optimizing the selection of items to include in a shipment for a logistics company. The company has a fleet of delivery vehicles, each with a maximum weight capacity of **7,125 kilograms**. There are **93 unique items** available for shipment, each with a specific **value** (representing the revenue generated if the item is delivered) and a **weight** (representing the space it occupies in the vehicle). Your goal is to select a combination of items that maximizes the total revenue while ensuring the total weight of the selected items does not exceed the vehicle's capacity.

#### Item Details:
Each item has a unique identifier (e.g., Item 0, Item 1, ..., Item 92) and the following attributes:
- **Value (Revenue):** The revenue generated if the item is delivered. For example, Item 0 generates **400 units of revenue**, Item 1 generates **616 units**, and so on, up to Item 92, which generates **654 units**.
- **Weight:** The weight of the item in kilograms. For example, Item 0 weighs **82 kilograms**, Item 1 weighs **102 kilograms**, and so on, up to Item 92, which weighs **115 kilograms**.

#### Objective:
Your objective is to **maximize the total revenue** generated from the selected items. This means choosing a subset of items whose combined revenue is as high as possible, while ensuring their total weight does not exceed **7,125 kilograms**.

#### Constraints:
1. **Weight Capacity Constraint:** The total weight of all selected items must not exceed **7,125 kilograms**. For example, if you select Item 0 (82 kg), Item 1 (102 kg), and Item 2 (114 kg), their combined weight is **298 kilograms**, which is within the limit. However, you must ensure that the cumulative weight of all selected items does not exceed the vehicle's capacity.
2. **Binary Selection:** Each item can either be **fully included** (selected) or **fully excluded** (not selected) from the shipment. Partial selections are not allowed.

#### Example:
Suppose you are considering the following items:
- Item 0: Revenue = 400, Weight = 82 kg
- Item 1: Revenue = 616, Weight = 102 kg
- Item 2: Revenue = 691, Weight = 114 kg

If you select all three items, the total revenue would be **400 + 616 + 691 = 1,707 units**, and the total weight would be **82 + 102 + 114 = 298 kg**, which is well within the vehicle's capacity. However, you must evaluate all 93 items to determine the optimal combination that maximizes revenue without exceeding the weight limit.

#### Final Goal:
Determine the optimal subset of items to include in the shipment such that:
- The total revenue is maximized.
- The total weight of the selected items does not exceed **7,125 kilograms**.
- Each item is either fully included or fully excluded from the shipment.

This problem requires careful consideration of the trade-offs between the revenue generated by each item and its associated weight, ensuring the most profitable combination is selected without overloading the vehicle.
```

### 4. spec.json (`spec` and `warnings`)

```json
"capacity": {"base":7125,"perturb":{"mode":"rel","r":0.25}}
"values": {"base":[400,616,691,654],"perturb":{"mode":"rel","r":0.3}}
"weights": {"base":[82,102,114,115],"perturb":{"mode":"rel","r":0.25}}
```

Warnings:

```
none
```

### 5. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    values = params["values"]
    weights = params["weights"]

    n = len(values)
    items = list(range(n))

    model = pyo.ConcreteModel()
    model.x = pyo.Var(items, within=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(values[i] * model.x[i] for i in items),
        sense=pyo.maximize,
    )

    model.weight_con = pyo.Constraint(
        expr=sum(weights[i] * model.x[i] for i in items) <= capacity
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"I":"0..92"},"params":{"capacity":"scalar from params['capacity']","values":"I-indexed from params['values']","weights":"I-indexed from params['weights']"},"variables":{"selected[i]":"Binary for i in I"},"constraints":["sum(weights[i]*selected[i] for i in I) <= capacity"],"objective":"maximize sum(values[i]*selected[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.item_set = pyo.RangeSet(0, 92)

    model.vehicle_capacity = pyo.Param(
        initialize=params["capacity"],
        within=pyo.Reals,
    )
    model.item_value = pyo.Param(
        model.item_set,
        initialize=lambda mdl, i: params["values"][i],
        within=pyo.Reals,
    )
    model.item_weight = pyo.Param(
        model.item_set,
        initialize=lambda mdl, i: params["weights"][i],
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.item_set, domain=pyo.Binary)

    model.weight_limit = pyo.Constraint(
        expr=sum(
            model.item_weight[i] * model.selected[i]
            for i in model.item_set
        ) <= model.vehicle_capacity
    )

    model.total_revenue = pyo.Objective(
        expr=sum(
            model.item_value[i] * model.selected[i]
            for i in model.item_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB


def solve(params):
    capacity = params["capacity"]
    values = params["values"]
    weights = params["weights"]

    n = len(values)

    model = gp.Model("knapsack")
    model.setParam("OutputFlag", 0)

    x = model.addVars(n, vtype=GRB.BINARY, name="x")

    model.setObjective(gp.quicksum(values[i] * x[i] for i in range(n)), GRB.MAXIMIZE)

    model.addConstr(
        gp.quicksum(weights[i] * x[i] for i in range(n)) <= capacity,
        name="weight_capacity"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 6. Objective values

Rules that certify it: gate, panel_base_2of3, ind_gate.

#### param_screen

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 2361.0 (optimal) | none (crash:initialize=lambda mdl, i: params["values"][i], \| ~~~~~~~~~~~~~~~~^^^ \| IndexError: list index out of range) | 2361.0 (optimal) |
| 1 | 2141.8878937971267 (optimal) | none (crash:initialize=lambda mdl, i: params["values"][i], \| ~~~~~~~~~~~~~~~~^^^ \| IndexError: list index out of range) | 2141.8878937971267 (optimal) |
| 2 | 1980.9781355962384 (optimal) | none (crash:initialize=lambda mdl, i: params["values"][i], \| ~~~~~~~~~~~~~~~~^^^ \| IndexError: list index out of range) | 1980.9781355962384 (optimal) |
| 3 | 2375.053393643919 (optimal) | none (crash:initialize=lambda mdl, i: params["values"][i], \| ~~~~~~~~~~~~~~~~^^^ \| IndexError: list index out of range) | 2375.053393643919 (optimal) |
| 4 | 2700.2179243148057 (optimal) | none (crash:initialize=lambda mdl, i: params["values"][i], \| ~~~~~~~~~~~~~~~~^^^ \| IndexError: list index out of range) | 2700.2179243148057 (optimal) |
| 5 | 2635.475798876472 (optimal) | none (crash:initialize=lambda mdl, i: params["values"][i], \| ~~~~~~~~~~~~~~~~^^^ \| IndexError: list index out of range) | 2635.4757988764713 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 2361.0 (optimal) | none (crash:initialize=lambda mdl, i: params["values"][i], \| ~~~~~~~~~~~~~~~~^^^ \| IndexError: list index out of range) | 2361.0 (optimal) |
| 1 | 2141.8878937971267 (optimal) | none (crash:initialize=lambda mdl, i: params["values"][i], \| ~~~~~~~~~~~~~~~~^^^ \| IndexError: list index out of range) | 2141.8878937971267 (optimal) |
| 2 | 1980.9781355962384 (optimal) | none (crash:initialize=lambda mdl, i: params["values"][i], \| ~~~~~~~~~~~~~~~~^^^ \| IndexError: list index out of range) | 1980.9781355962384 (optimal) |
| 3 | 2375.053393643919 (optimal) | none (crash:initialize=lambda mdl, i: params["values"][i], \| ~~~~~~~~~~~~~~~~^^^ \| IndexError: list index out of range) | 2375.053393643919 (optimal) |
| 4 | 2700.2179243148057 (optimal) | none (crash:initialize=lambda mdl, i: params["values"][i], \| ~~~~~~~~~~~~~~~~^^^ \| IndexError: list index out of range) | 2700.2179243148057 (optimal) |
| 5 | 2635.475798876472 (optimal) | none (crash:initialize=lambda mdl, i: params["values"][i], \| ~~~~~~~~~~~~~~~~^^^ \| IndexError: list index out of range) | 2635.4757988764713 (optimal) |


## 4. sample_65 (stream (OptMATH-295))

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `sample_65` |
| Set | stream (OptMATH-295) |
| Source record | OptMATH-Train record 162141 |
| Optimization sense | not determined from the problem text (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 780930.0 |
| Label | 772406.0 |
| Rules that certify it | gate, panel_base_2of3, ind_gate (values: 780930.0) |
| Label source | `artifacts/v2/optmath_295/problems.csv`, OptMATH-Train record 162141, field `answer`; the dataset stores no solution |

### 2. Certifying clique of panel_base_2of3 and values at instance 0

Families that agree at the stated instance (abs(a-b) <= 1e-4*max(1,|a|,|b|)): B (GPT-6.1 Sol) and C (Claude Sonnet 5.5). The third family: A (DeepSeek-V4-Flash) returns 770796.0.

| Family | Program | Value at instance 0 | Status at instance 0 | In the certifying clique | Matches the label (round_aware) |
|---|---|---|---|---|---|
| A (DeepSeek-V4-Flash) | A-direct.py | 770796.0 | optimal | no | no |
| B (GPT-6.1 Sol) | B-structured.py | 780930.0 | optimal | yes | no |
| C (Claude Sonnet 5.5) | C-direct.py | 780930.0 | optimal | yes | no |

### 3. Problem text

```
Imagine you are managing a network of distribution centers and retail stores for a large retail chain. Your goal is to minimize the total cost of operating the distribution centers and shipping products to meet the demand of each retail store. Here’s the situation:

You have **6 distribution centers** (facilities) that can be opened or closed, and **11 retail stores** (customers) that need to be supplied with products. Each distribution center has a fixed cost to operate, and each shipment from a distribution center to a retail store incurs a variable cost. Additionally, each distribution center has a limited capacity for how much it can ship, and each retail store has a specific demand that must be met.

#### Key Details:
1. **Fixed Costs for Opening Distribution Centers**:
   - Opening Distribution Center 0 costs **100,274 units**.
   - Opening Distribution Center 1 costs **96,413 units**.
   - Opening Distribution Center 2 costs **103,573 units**.
   - Opening Distribution Center 3 costs **103,557 units**.
   - Opening Distribution Center 4 costs **104,460 units**.
   - Opening Distribution Center 5 costs **97,217 units**.

2. **Variable Shipping Costs**:
   - Shipping costs vary depending on the distribution center and retail store. For example:
     - Shipping from Distribution Center 0 to Retail Store 0 costs **61 units**.
     - Shipping from Distribution Center 1 to Retail Store 0 costs **65 units**.
     - Shipping from Distribution Center 2 to Retail Store 0 costs **68 units**.
     - Shipping from Distribution Center 3 to Retail Store 0 costs **63 units**.
     - Shipping from Distribution Center 4 to Retail Store 0 costs **62 units**.
     - Shipping from Distribution Center 5 to Retail Store 0 costs **69 units**.
   - Similar costs apply for all other retail stores and distribution centers.

3. **Retail Store Demands**:
   - Retail Store 0 requires **400 units**.
   - Retail Store 1 requires **387 units**.
   - Retail Store 2 requires **398 units**.
   - Retail Store 3 requires **404 units**.
   - Retail Store 4 requires **389 units**.
   - Retail Store 5 requires **384 units**.
   - Retail Store 6 requires **412 units**.
   - Retail Store 7 requires **410 units**.
   - Retail Store 8 requires **417 units**.
   - Retail Store 9 requires **402 units**.
   - Retail Store 10 requires **397 units**.

4. **Distribution Center Capacities**:
   - Distribution Center 0 can handle a maximum of **964 units** if opened.
   - Distribution Center 1 can handle a maximum of **973 units** if opened.
   - Distribution Center 2 can handle a maximum of **983 units** if opened.
   - Distribution Center 3 can handle a maximum of **1,041 units** if opened.
   - Distribution Center 4 can handle a maximum of **963 units** if opened.
   - Distribution Center 5 can handle a maximum of **1,003 units** if opened.

#### Constraints:
1. **Demand Satisfaction**:
   - The total amount shipped to each retail store from all distribution centers must exactly match its demand. For example:
     - Retail Store 0 must receive exactly **400 units** from one or more distribution centers.
     - Retail Store 1 must receive exactly **387 units**, and so on.

2. **Capacity Limits**:
   - No distribution center can ship more than its capacity. For example:
     - If Distribution Center 0 is opened, it cannot ship more than **964 units** in total across all retail stores.
     - If Distribution Center 1 is opened, it cannot ship more than **973 units**, and so on.

3. **Logical Constraints**:
   - A distribution center can only ship products to retail stores if it is opened. For example:
     - If Distribution Center 0 is not opened, no shipments can be made from it to any retail store.
     - If Distribution Center 1 is opened, shipments can be made to any retail store, but only up to its capacity.

#### Objective:
Your goal is to determine which distribution centers to open and how much to ship from each opened distribution center to each retail store to **minimize the total cost**. The total cost includes:
- The fixed costs of opening the distribution centers.
- The variable shipping costs for all shipments made.

By carefully balancing these costs and constraints, you aim to ensure that all retail stores receive their required products at the lowest possible total expense.
```

### 4. spec.json (`spec` and `warnings`)

```json
"fixed_costs": {"base":[100274,96413,103573,103557,104460,97217],"perturb":{"mode":"rel","r":0.25}}
"shipping_costs_col0": {"base":[61,65,68,63,62,69],"perturb":{"mode":"rel","r":0.4}}
"demands": {"base":[400,387,398,404,389,384,412,410,417,402,397],"perturb":{"mode":"rel","r":0.2}}
"capacities": {"base":[964,973,983,1041,963,1003],"perturb":{"mode":"rel","r":0.25}}
```

Warnings:

```
none
```

### 5. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_costs = params["fixed_costs"]
    ship_col0 = params["shipping_costs_col0"]
    demands = params["demands"]
    capacities = params["capacities"]

    n_fac = 6
    n_cus = 11

    # Build full shipping cost matrix. For column 0 use provided costs;
    # for other columns derive deterministic values from base costs.
    ship = {}
    for i in range(n_fac):
        for j in range(n_cus):
            if j == 0:
                ship[i, j] = ship_col0[i]
            else:
                ship[i, j] = ship_col0[i] + ((i + 2 * j) % 7) - 3

    model = pyo.ConcreteModel()

    model.FAC = pyo.RangeSet(0, n_fac - 1)
    model.CUS = pyo.RangeSet(0, n_cus - 1)

    model.x = pyo.Var(model.FAC, model.CUS, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.FAC, domain=pyo.Binary)

    def obj_rule(m):
        return sum(fixed_costs[i] * m.y[i] for i in m.FAC) + \
               sum(ship[i, j] * m.x[i, j] for i in m.FAC for j in m.CUS)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.FAC) == demands[j]

    model.demand_con = pyo.Constraint(model.CUS, rule=demand_rule)

    def cap_rule(m, i):
        return sum(m.x[i, j] for j in m.CUS) <= capacities[i] * m.y[i]

    model.cap_con = pyo.Constraint(model.FAC, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"facilities":"0..5","stores":"0..10"},"params":{"fixed_costs":"params['fixed_costs'][i]","shipping_costs_col0":"params['shipping_costs_col0'][i]","demands":"params['demands'][j]","capacities":"params['capacities'][i]"},"assumption":"Because only column 0 shipping costs are provided, use shipping_costs_col0[i] for every store j.","variables":{"opened[i]":"Binary","shipped[i,j]":"NonNegativeReals"},"constraints":["sum_i shipped[i,j] == demands[j] for each store j","sum_j shipped[i,j] <= capacities[i]*opened[i] for each facility i"],"objective":"minimize sum_i fixed_costs[i]*opened[i] + sum_i,j shipping_costs_col0[i]*shipped[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_costs = params["fixed_costs"]
    shipping_costs_col0 = params["shipping_costs_col0"]
    demands = params["demands"]
    capacities = params["capacities"]

    model = pyo.ConcreteModel()

    model.facilities = pyo.RangeSet(0, 5)
    model.stores = pyo.RangeSet(0, 10)

    model.fixed_cost = pyo.Param(
        model.facilities,
        initialize={i: fixed_costs[i] for i in model.facilities},
        within=pyo.Reals,
    )
    model.shipping_cost = pyo.Param(
        model.facilities,
        initialize={i: shipping_costs_col0[i] for i in model.facilities},
        within=pyo.Reals,
    )
    model.store_demand = pyo.Param(
        model.stores,
        initialize={j: demands[j] for j in model.stores},
        within=pyo.NonNegativeReals,
    )
    model.facility_capacity = pyo.Param(
        model.facilities,
        initialize={i: capacities[i] for i in model.facilities},
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.facilities, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.facilities, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(model, j):
        return (
            sum(model.shipped[i, j] for i in model.facilities)
            == model.store_demand[j]
        )

    model.demand_balance = pyo.Constraint(model.stores, rule=demand_rule)

    def capacity_rule(model, i):
        return (
            sum(model.shipped[i, j] for j in model.stores)
            <= model.facility_capacity[i] * model.opened[i]
        )

    model.capacity_limit = pyo.Constraint(model.facilities, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[i] * model.opened[i] for i in model.facilities
        )
        + sum(
            model.shipping_cost[i] * model.shipped[i, j]
            for i in model.facilities
            for j in model.stores
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
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_costs = params["fixed_costs"]
    shipping_costs_col0 = params["shipping_costs_col0"]
    demands = params["demands"]
    capacities = params["capacities"]

    num_facilities = 6
    num_customers = 11

    # shipping_costs_col0 gives costs from each DC to store 0 only.
    # The problem only provides column 0 shipping costs explicitly.
    # We use shipping_costs_col0[i] as the per-unit cost from DC i to any customer
    # (the problem description only gives store-0 costs; we apply them uniformly).
    # This matches the data structure implied by the param name.

    model = gp.Model("facility_location")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # open_dc[i]: binary, 1 if DC i is opened
    open_dc = model.addVars(num_facilities, vtype=GRB.BINARY, name="open_dc")

    # ship[i, j]: continuous, units shipped from DC i to store j
    ship = model.addVars(num_facilities, num_customers, lb=0.0, name="ship")

    # Objective: fixed costs + shipping costs
    obj = gp.quicksum(fixed_costs[i] * open_dc[i] for i in range(num_facilities))
    obj += gp.quicksum(
        shipping_costs_col0[i] * ship[i, j]
        for i in range(num_facilities)
        for j in range(num_customers)
    )
    model.setObjective(obj, GRB.MINIMIZE)

    # Demand satisfaction: each store j receives exactly its demand
    for j in range(num_customers):
        model.addConstr(
            gp.quicksum(ship[i, j] for i in range(num_facilities)) == demands[j],
            name=f"demand_{j}"
        )

    # Capacity limits: DC i cannot exceed its capacity, and only if opened
    for i in range(num_facilities):
        model.addConstr(
            gp.quicksum(ship[i, j] for j in range(num_customers)) <= capacities[i] * open_dc[i],
            name=f"capacity_{i}"
        )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}
```

### 6. Objective values

Rules that certify it: gate, panel_base_2of3, ind_gate.

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 770796.0 (optimal) | 780930.0 (optimal) | 780930.0 (optimal) |
| 1 | 688877.4917569348 (optimal) | 698683.8927934892 (optimal) | 698683.8927934893 (optimal) |
| 2 | 707882.7785734287 (optimal) | 717468.136045871 (optimal) | 717468.136045871 (optimal) |
| 3 | 749538.8134196365 (optimal) | 759866.021859861 (optimal) | 759866.021859861 (optimal) |
| 4 | 702699.9597171742 (optimal) | 711414.017418817 (optimal) | 711414.017418817 (optimal) |
| 5 | 730947.3693894732 (optimal) | 738232.4137927899 (optimal) | 738232.4137927898 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 770796.0 (optimal) | 780930.0 (optimal) | 780930.0 (optimal) |
| 1 | 688877.4917569348 (optimal) | 698683.8927934892 (optimal) | 698683.8927934893 (optimal) |
| 2 | 707882.7785734287 (optimal) | 717468.136045871 (optimal) | 717468.136045871 (optimal) |
| 3 | 749538.8134196365 (optimal) | 759866.021859861 (optimal) | 759866.021859861 (optimal) |
| 4 | 702699.9597171742 (optimal) | 711414.017418817 (optimal) | 711414.017418817 (optimal) |
| 5 | 730947.3693894732 (optimal) | 738232.4137927899 (optimal) | 738232.4137927898 (optimal) |


## 5. sample_77 (stream (OptMATH-295))

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `sample_77` |
| Set | stream (OptMATH-295) |
| Source record | OptMATH-Train record 26476 |
| Optimization sense | not determined from the problem text (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 17994.0 |
| Label | 17514.0 |
| Rules that certify it | gate, panel_base_2of3, ind_gate (values: 17994.0) |
| Label source | `artifacts/v2/optmath_295/problems.csv`, OptMATH-Train record 26476, field `answer`; the dataset stores no solution |

### 2. Certifying clique of panel_base_2of3 and values at instance 0

Families that agree at the stated instance (abs(a-b) <= 1e-4*max(1,|a|,|b|)): A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5). The third family: B (GPT-6.1 Sol) returns 17514.0.

| Family | Program | Value at instance 0 | Status at instance 0 | In the certifying clique | Matches the label (round_aware) |
|---|---|---|---|---|---|
| A (DeepSeek-V4-Flash) | A-direct.py | 17994.0 | optimal | yes | no |
| B (GPT-6.1 Sol) | B-structured.py | 17514.0 | optimal | no | yes |
| C (Claude Sonnet 5.5) | C-direct.py | 17994.0 | optimal | yes | no |

### 3. Problem text

```
You are responsible for managing the assignment of aircraft to various flight routes for an airline company. The goal is to minimize the total operational costs while ensuring that all flight routes are adequately serviced and that the availability of each aircraft type is not exceeded.

#### Aircraft and Routes:
- There are **8 types of aircraft** (aircraft_0 to aircraft_7) available for assignment.
- There are **8 flight routes** (route_0 to route_7) that need to be serviced.

#### Aircraft Availability:
- **Aircraft_0** can be assigned to a maximum of **5 routes**.
- **Aircraft_1** can be assigned to a maximum of **5 routes**.
- **Aircraft_2** can be assigned to a maximum of **3 routes**.
- **Aircraft_3** can be assigned to a maximum of **3 routes**.
- **Aircraft_4** can be assigned to a maximum of **6 routes**.
- **Aircraft_5** can be assigned to a maximum of **6 routes**.
- **Aircraft_6** can be assigned to a maximum of **5 routes**.
- **Aircraft_7** can be assigned to a maximum of **4 routes**.

#### Route Demand:
Each route has a specific demand that must be met by the combined capabilities of the assigned aircraft. The demand for each route is as follows:
- **Route_0** requires a total capacity of **102 units**.
- **Route_1** requires a total capacity of **132 units**.
- **Route_2** requires a total capacity of **122 units**.
- **Route_3** requires a total capacity of **117 units**.
- **Route_4** requires a total capacity of **119 units**.
- **Route_5** requires a total capacity of **133 units**.
- **Route_6** requires a total capacity of **130 units**.
- **Route_7** requires a total capacity of **139 units**.

#### Aircraft Capabilities and Costs:
Each aircraft type has a specific capacity contribution and cost associated with assigning it to a particular route. The costs and capacities are as follows:

- **Aircraft_0**:
  - Route_0: Cost = **1068**, Capacity = **57**
  - Route_1: Cost = **1041**, Capacity = **53**
  - Route_2: Cost = **1270**, Capacity = **69**
  - Route_3: Cost = **1438**, Capacity = **52**
  - Route_4: Cost = **1062**, Capacity = **68**
  - Route_5: Cost = **1449**, Capacity = **70**
  - Route_6: Cost = **1144**, Capacity = **75**
  - Route_7: Cost = **1329**, Capacity = **64**

- **Aircraft_1**:
  - Route_0: Cost = **1118**, Capacity = **72**
  - Route_1: Cost = **1144**, Capacity = **64**
  - Route_2: Cost = **1374**, Capacity = **71**
  - Route_3: Cost = **1235**, Capacity = **51**
  - Route_4: Cost = **1055**, Capacity = **79**
  - Route_5: Cost = **1084**, Capacity = **53**
  - Route_6: Cost = **1168**, Capacity = **71**
  - Route_7: Cost = **1094**, Capacity = **61**

- **Aircraft_2**:
  - Route_0: Cost = **1477**, Capacity = **71**
  - Route_1: Cost = **1111**, Capacity = **55**
  - Route_2: Cost = **1479**, Capacity = **80**
  - Route_3: Cost = **1120**, Capacity = **57**
  - Route_4: Cost = **1422**, Capacity = **77**
  - Route_5: Cost = **1306**, Capacity = **59**
  - Route_6: Cost = **1389**, Capacity = **50**
  - Route_7: Cost = **1079**, Capacity = **62**

- **Aircraft_3**:
  - Route_0: Cost = **1374**, Capacity = **52**
  - Route_1: Cost = **1460**, Capacity = **55**
  - Route_2: Cost = **1285**, Capacity = **54**
  - Route_3: Cost = **1080**, Capacity = **74**
  - Route_4: Cost = **1218**, Capacity = **68**
  - Route_5: Cost = **1415**, Capacity = **75**
  - Route_6: Cost = **1242**, Capacity = **63**
  - Route_7: Cost = **1038**, Capacity = **60**

- **Aircraft_4**:
  - Route_0: Cost = **1443**, Capacity = **51**
  - Route_1: Cost = **1177**, Capacity = **61**
  - Route_2: Cost = **1341**, Capacity = **79**
  - Route_3: Cost = **1078**, Capacity = **73**
  - Route_4: Cost = **1465**, Capacity = **73**
  - Route_5: Cost = **1201**, Capacity = **76**
  - Route_6: Cost = **1155**, Capacity = **58**
  - Route_7: Cost = **1218**, Capacity = **53**

- **Aircraft_5**:
  - Route_0: Cost = **1056**, Capacity = **61**
  - Route_1: Cost = **1250**, Capacity = **74**
  - Route_2: Cost = **1321**, Capacity = **71**
  - Route_3: Cost = **1141**, Capacity = **68**
  - Route_4: Cost = **1418**, Capacity = **62**
  - Route_5: Cost = **1440**, Capacity = **58**
  - Route_6: Cost = **1062**, Capacity = **58**
  - Route_7: Cost = **1229**, Capacity = **67**

- **Aircraft_6**:
  - Route_0: Cost = **1096**, Capacity = **75**
  - Route_1: Cost = **1012**, Capacity = **60**
  - Route_2: Cost = **1133**, Capacity = **72**
  - Route_3: Cost = **1038**, Capacity = **64**
  - Route_4: Cost = **1135**, Capacity = **78**
  - Route_5: Cost = **1037**, Capacity = **53**
  - Route_6: Cost = **1423**, Capacity = **70**
  - Route_7: Cost = **1293**, Capacity = **73**

- **Aircraft_7**:
  - Route_0: Cost = **1264**, Capacity = **66**
  - Route_1: Cost = **1497**, Capacity = **63**
  - Route_2: Cost = **1489**, Capacity = **52**
  - Route_3: Cost = **1395**, Capacity = **78**
  - Route_4: Cost = **1428**, Capacity = **57**
  - Route_5: Cost = **1286**, Capacity = **50**
  - Route_6: Cost = **1042**, Capacity = **57**
  - Route_7: Cost = **1050**, Capacity = **72**

#### Objective:
Your task is to assign the available aircraft to the routes in such a way that the total operational cost is minimized, while ensuring that:
1. The total number of routes assigned to each aircraft does not exceed its availability.
2. The combined capacity of the assigned aircraft meets or exceeds the demand for each route.

The assignment must be made in whole numbers, as partial assignments are not feasible.

#### Constraints:
- **Aircraft Availability Constraints**: The total number of routes assigned to each aircraft must not exceed its availability.
- **Route Demand Constraints**: The combined capacity of the assigned aircraft for each route must meet or exceed the route's demand.

Your goal is to determine the optimal assignment of aircraft to routes that minimizes the total cost while satisfying all the constraints.
```

### 4. spec.json (`spec` and `warnings`)

```json
"aircraft_availability": {"base":[5,5,3,3,6,6,5,4],"perturb":{"mode":"rel","r":0.3}}
"route_demand": {"base":[102,132,122,117,119,133,130,139],"perturb":{"mode":"rel","r":0.15}}
"cost_matrix": {"base":[[1068,1041,1270,1438,1062,1449,1144,1329],[1118,1144,1374,1235,1055,1084,1168,1094],[1477,1111,1479,1120,1422,1306,1389,1079],[1374,1460,1285,1080,1218,1415,1242,1038],[1443,1177,1341,1078,1465,1201,1155,1218],[1056,1250,1321,1141,1418,1440,1062,1229],[1096,1012,1133,1038,1135,1037,1423,1293],[1264,1497,1489,1395,1428,1286,1042,1050]],"perturb":{"mode":"rel","r":0.2}}
"capacity_matrix": {"base":[[57,53,69,52,68,70,75,64],[72,64,71,51,79,53,71,61],[71,55,80,57,77,59,50,62],[52,55,54,74,68,75,63,60],[51,61,79,73,73,76,58,53],[61,74,71,68,62,58,58,67],[75,60,72,64,78,53,70,73],[66,63,52,78,57,50,57,72]],"perturb":{"mode":"rel","r":0.15}}
```

Warnings:

```
[aircraft_availability] malformed abs bounds (lo/hi not scalar); fell back to rel +/-30% around base
```

### 5. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    aircraft = list(range(8))
    routes = list(range(8))

    availability = params["aircraft_availability"]
    demand = params["route_demand"]
    cost = params["cost_matrix"]
    cap = params["capacity_matrix"]

    model = pyo.ConcreteModel()

    model.A = pyo.Set(initialize=aircraft)
    model.R = pyo.Set(initialize=routes)

    model.x = pyo.Var(model.A, model.R, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.A for j in m.R)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def avail_rule(m, i):
        return sum(m.x[i, j] for j in m.R) <= availability[i]

    model.avail_con = pyo.Constraint(model.A, rule=avail_rule)

    def demand_rule(m, j):
        return sum(cap[i][j] * m.x[i, j] for i in m.A) >= demand[j]

    model.demand_con = pyo.Constraint(model.R, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"I":"0..7","J":"0..7"},"params":{"aircraft_availability":"A[i]","route_demand":"D[j]","cost_matrix":"C[i,j]","capacity_matrix":"Q[i,j]"},"variables":{"x[i,j]":{"type":"nonnegative_integer","meaning":"number of aircraft of type i assigned to route j"}},"constraints":["sum(j in J, x[i,j]) <= A[i] for each i in I","sum(i in I, Q[i,j]*x[i,j]) >= D[j] for each j in J"],"objective":"minimize sum(i in I, j in J, C[i,j]*x[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    aircraft_availability = params["aircraft_availability"]
    route_demand = params["route_demand"]
    cost_matrix = params["cost_matrix"]
    capacity_matrix = params["capacity_matrix"]

    model = pyo.ConcreteModel()
    model.aircraft = pyo.RangeSet(0, 7)
    model.routes = pyo.RangeSet(0, 7)

    model.availability = pyo.Param(
        model.aircraft,
        initialize=lambda mdl, i: aircraft_availability[i],
    )
    model.demand = pyo.Param(
        model.routes,
        initialize=lambda mdl, j: route_demand[j],
    )
    model.operating_cost = pyo.Param(
        model.aircraft,
        model.routes,
        initialize=lambda mdl, i, j: cost_matrix[i][j],
    )
    model.capacity = pyo.Param(
        model.aircraft,
        model.routes,
        initialize=lambda mdl, i, j: capacity_matrix[i][j],
    )

    model.x = pyo.Var(
        model.aircraft,
        model.routes,
        domain=pyo.NonNegativeIntegers,
    )

    def availability_rule(mdl, i):
        return (
            sum(mdl.x[i, j] for j in mdl.routes)
            <= mdl.availability[i]
        )

    model.availability_constraints = pyo.Constraint(
        model.aircraft,
        rule=availability_rule,
    )

    def demand_rule(mdl, j):
        return (
            sum(
                mdl.capacity[i, j] * mdl.x[i, j]
                for i in mdl.aircraft
            )
            >= mdl.demand[j]
        )

    model.demand_constraints = pyo.Constraint(
        model.routes,
        rule=demand_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.operating_cost[i, j] * model.x[i, j]
            for i in model.aircraft
            for j in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when no feasible solution can be loaded.
        # Still determine success exclusively by objective retrieval below.
        if "feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB


def solve(params):
    aircraft_availability = params["aircraft_availability"]
    route_demand = params["route_demand"]
    cost_matrix = params["cost_matrix"]
    capacity_matrix = params["capacity_matrix"]

    n_aircraft = 8
    n_routes = 8

    model = gp.Model("airline_assignment")
    model.Params.OutputFlag = 0

    x = model.addVars(n_aircraft, n_routes, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(
            cost_matrix[i][j] * x[i, j]
            for i in range(n_aircraft)
            for j in range(n_routes)
        ),
        GRB.MINIMIZE,
    )

    for i in range(n_aircraft):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_routes)) <= aircraft_availability[i],
            name=f"availability_{i}",
        )

    for j in range(n_routes):
        model.addConstr(
            gp.quicksum(
                capacity_matrix[i][j] * x[i, j] for i in range(n_aircraft)
            ) >= route_demand[j],
            name=f"demand_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "failed"}
```

### 6. Objective values

Rules that certify it: gate, panel_base_2of3, ind_gate.

#### param_screen

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 17994.0 (optimal) | 17514.0 (optimal) | 17994.0 (optimal) |
| 1 | 16348.20386451807 (optimal) | 16014.981671630141 (optimal) | 16348.203864518066 (optimal) |
| 2 | 16174.65527401617 (optimal) | 15812.125879721048 (optimal) | 16174.65527401617 (optimal) |
| 3 | 17742.787286927418 (optimal) | 17144.424805279676 (optimal) | 17742.787286927414 (optimal) |
| 4 | 17764.621713524488 (optimal) | 17043.519927109275 (optimal) | 17764.621713524488 (optimal) |
| 5 | 16758.78622133635 (optimal) | 16270.87868184432 (optimal) | 16758.786221336348 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 17994.0 (optimal) | 17514.0 (optimal) | 17994.0 (optimal) |
| 1 | 16348.20386451807 (optimal) | 16014.981671630141 (optimal) | 16348.203864518066 (optimal) |
| 2 | 16174.65527401617 (optimal) | 15812.125879721048 (optimal) | 16174.65527401617 (optimal) |
| 3 | 17742.787286927418 (optimal) | 17144.424805279676 (optimal) | 17742.787286927414 (optimal) |
| 4 | 17764.621713524488 (optimal) | 17043.519927109275 (optimal) | 17764.621713524488 (optimal) |
| 5 | 16758.78622133635 (optimal) | 16270.87868184432 (optimal) | 16758.786221336348 (optimal) |


## 6. sample_147 (stream (OptMATH-295))

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `sample_147` |
| Set | stream (OptMATH-295) |
| Source record | OptMATH-Train record 28743 |
| Optimization sense | not determined from the problem text (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 2927.0 |
| Label | 3140.0 |
| Rules that certify it | gate, panel_base_2of3, ind_gate (values: 2927.0) |
| Label source | `artifacts/v2/optmath_295/problems.csv`, OptMATH-Train record 28743, field `answer`; the dataset stores no solution |

### 2. Certifying clique of panel_base_2of3 and values at instance 0

Families that agree at the stated instance (abs(a-b) <= 1e-4*max(1,|a|,|b|)): A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5). The third family: B (GPT-6.1 Sol) returns 3880.9999999999995.

| Family | Program | Value at instance 0 | Status at instance 0 | In the certifying clique | Matches the label (round_aware) |
|---|---|---|---|---|---|
| A (DeepSeek-V4-Flash) | A-direct.py | 2927.0 | optimal | yes | no |
| B (GPT-6.1 Sol) | B-structured.py | 3880.9999999999995 | optimal | no | no |
| C (Claude Sonnet 5.5) | C-direct.py | 2927.0 | optimal | yes | no |

### 3. Problem text

```
Minimize the total operational cost of a power generation system over four consecutive time periods. The system includes two types of generators: Type 0 and Type 1. The total cost consists of a base cost of 75 units for each Type 0 generator and 79 units for each Type 1 generator that is operational in a given period, a variable cost of 4 units per megawatt of power generated by Type 0 generators and 3 units per megawatt for Type 1 generators, and a startup cost of 381 units for each Type 0 generator and 360 units for each Type 1 generator that is activated in a given period. 

The number of Type 0 generators operating in any period cannot exceed 3, and the number of Type 1 generators operating in any period cannot exceed 4. The total power generated by all generators in each period must meet or exceed the demand for that period, which is 165 MW in Period 0, 181 MW in Period 1, 203 MW in Period 2, and 216 MW in Period 3. 

Each Type 0 generator must produce at least 50 MW and no more than 131 MW when operational, and each Type 1 generator must produce at least 48 MW and no more than 145 MW when operational. The total maximum possible output of all generators in each period must be at least 15% higher than the demand for that period, ensuring a buffer for unexpected increases in demand or generator failures. 

The number of Type 0 generators starting up in Period 0 cannot exceed 2, and for subsequent periods, the number of startups is limited by the number of generators that were operational in the previous period. Similarly, the number of Type 1 generators starting up in Period 0 cannot exceed 1, and for subsequent periods, the number of startups is limited by the number of generators that were operational in the previous period. 

The variables representing the number of generators and the number of startups are general integer variables. The solution must determine the optimal number of generators to operate, the power output for each generator type, and the number of startups required in each period to minimize the total operational cost while ensuring that all demand and operational constraints are satisfied.
```

### 4. spec.json (`spec` and `warnings`)

```json
"base_cost_type0": {"base":75,"perturb":{"mode":"rel","r":0.4}}
"base_cost_type1": {"base":79,"perturb":{"mode":"rel","r":0.4}}
"var_cost_type0": {"base":4,"perturb":{"mode":"rel","r":0.5}}
"var_cost_type1": {"base":3,"perturb":{"mode":"rel","r":0.5}}
"startup_cost_type0": {"base":381,"perturb":{"mode":"rel","r":0.5}}
"startup_cost_type1": {"base":360,"perturb":{"mode":"rel","r":0.5}}
"max_units_type0": {"base":3,"perturb":{"mode":"abs","lo":3.0,"hi":3.0,"integer":true}}
"max_units_type1": {"base":4,"perturb":{"mode":"abs","lo":4.0,"hi":4.0,"integer":true}}
"demand": {"base":[165,181,203,216],"perturb":{"mode":"rel","r":0.2}}
"min_output_type0": {"base":50,"perturb":{"mode":"rel","r":0.3}}
"max_output_type0": {"base":131,"perturb":{"mode":"rel","r":0.25}}
"min_output_type1": {"base":48,"perturb":{"mode":"rel","r":0.3}}
"max_output_type1": {"base":145,"perturb":{"mode":"rel","r":0.25}}
"reserve_margin": {"base":0.15,"perturb":{"mode":"abs","lo":0.0,"hi":0.35,"integer":false}}
"max_startup_type0_period0": {"base":2,"perturb":{"mode":"abs","lo":0.0,"hi":3.0,"integer":true}}
"max_startup_type1_period0": {"base":1,"perturb":{"mode":"abs","lo":0.0,"hi":4.0,"integer":true}}
"num_periods": {"base":4,"perturb":{"mode":"abs","lo":4.0,"hi":4.0,"integer":true}}
```

Warnings:

```
[max_units_type0] degenerate abs range (lo == hi); perturbation has no effect
[max_units_type1] degenerate abs range (lo == hi); perturbation has no effect
[num_periods] degenerate abs range (lo == hi); perturbation has no effect
```

### 5. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    T = params["num_periods"]

    base0 = params["base_cost_type0"]
    base1 = params["base_cost_type1"]
    var0 = params["var_cost_type0"]
    var1 = params["var_cost_type1"]
    start0 = params["startup_cost_type0"]
    start1 = params["startup_cost_type1"]

    max0 = params["max_units_type0"]
    max1 = params["max_units_type1"]

    demand = params["demand"]
    minout0 = params["min_output_type0"]
    maxout0 = params["max_output_type0"]
    minout1 = params["min_output_type1"]
    maxout1 = params["max_output_type1"]

    reserve = params["reserve_margin"]

    mstart0 = params["max_startup_type0_period0"]
    mstart1 = params["max_startup_type1_period0"]

    model = pyo.ConcreteModel()
    model.T = pyo.RangeSet(0, T - 1)

    model.n0 = pyo.Var(model.T, domain=pyo.NonNegativeIntegers, bounds=(0, max0))
    model.n1 = pyo.Var(model.T, domain=pyo.NonNegativeIntegers, bounds=(0, max1))
    model.g0 = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.g1 = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.s0 = pyo.Var(model.T, domain=pyo.NonNegativeIntegers)
    model.s1 = pyo.Var(model.T, domain=pyo.NonNegativeIntegers)

    def demand_rule(m, t):
        return m.g0[t] + m.g1[t] >= demand[t]

    model.demand_con = pyo.Constraint(model.T, rule=demand_rule)

    def reserve_rule(m, t):
        return maxout0 * m.n0[t] + maxout1 * m.n1[t] >= (1.0 + reserve) * demand[t]

    model.reserve_con = pyo.Constraint(model.T, rule=reserve_rule)

    def gen0_lo(m, t):
        return m.g0[t] >= minout0 * m.n0[t]

    def gen0_hi(m, t):
        return m.g0[t] <= maxout0 * m.n0[t]

    def gen1_lo(m, t):
        return m.g1[t] >= minout1 * m.n1[t]

    def gen1_hi(m, t):
        return m.g1[t] <= maxout1 * m.n1[t]

    model.gen0_lo_con = pyo.Constraint(model.T, rule=gen0_lo)
    model.gen0_hi_con = pyo.Constraint(model.T, rule=gen0_hi)
    model.gen1_lo_con = pyo.Constraint(model.T, rule=gen1_lo)
    model.gen1_hi_con = pyo.Constraint(model.T, rule=gen1_hi)

    model.s0[0].setlb(0)
    model.s0[0].setub(mstart0)
    model.s1[0].setlb(0)
    model.s1[0].setub(mstart1)

    def startup0_rule(m, t):
        return m.s0[t] <= m.n0[t - 1]

    def startup1_rule(m, t):
        return m.s1[t] <= m.n1[t - 1]

    model.startup0_con = pyo.Constraint(pyo.RangeSet(1, T - 1), rule=startup0_rule)
    model.startup1_con = pyo.Constraint(pyo.RangeSet(1, T - 1), rule=startup1_rule)

    def cost_rule(m):
        total = 0
        for t in m.T:
            total += base0 * m.n0[t] + base1 * m.n1[t]
            total += var0 * m.g0[t] + var1 * m.g1[t]
            total += start0 * m.s0[t] + start1 * m.s1[t]
        return total

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"K":[0,1],"T":"range(params['num_periods'])"},"params":{"base_cost":["base_cost_type0","base_cost_type1"],"var_cost":["var_cost_type0","var_cost_type1"],"startup_cost":["startup_cost_type0","startup_cost_type1"],"max_units":["max_units_type0","max_units_type1"],"min_output":["min_output_type0","min_output_type1"],"max_output":["max_output_type0","max_output_type1"],"initial_startup_cap":["max_startup_type0_period0","max_startup_type1_period0"],"demand":"demand[t]","reserve_margin":"reserve_margin","num_periods":"num_periods"},"variables":{"operating[k,t]":"nonnegative integer, <= max_units[k]","generation[k,t]":"nonnegative real","startups[k,t]":"nonnegative integer"},"constraints":["sum_k generation[k,t] >= demand[t]","generation[k,t] >= min_output[k]*operating[k,t]","generation[k,t] <= max_output[k]*operating[k,t]","sum_k max_output[k]*operating[k,t] >= (1+reserve_margin)*demand[t]","startups[k,0] = operating[k,0] (initially all units off)","startups[k,0] <= initial_startup_cap[k]","startups[k,t] >= operating[k,t]-operating[k,t-1], t>0","startups[k,t] <= operating[k,t-1], t>0"],"objective":"min sum_{k,t}(base_cost[k]*operating[k,t]+var_cost[k]*generation[k,t]+startup_cost[k]*startups[k,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_periods = int(params["num_periods"])
    if num_periods != params["num_periods"] or num_periods < 1:
        raise ValueError("num_periods must be a positive integer.")

    base_cost = {
        0: params["base_cost_type0"],
        1: params["base_cost_type1"],
    }
    var_cost = {
        0: params["var_cost_type0"],
        1: params["var_cost_type1"],
    }
    startup_cost = {
        0: params["startup_cost_type0"],
        1: params["startup_cost_type1"],
    }
    max_units = {
        0: params["max_units_type0"],
        1: params["max_units_type1"],
    }
    min_output = {
        0: params["min_output_type0"],
        1: params["min_output_type1"],
    }
    max_output = {
        0: params["max_output_type0"],
        1: params["max_output_type1"],
    }
    initial_startup_cap = {
        0: params["max_startup_type0_period0"],
        1: params["max_startup_type1_period0"],
    }
    demand = params["demand"]
    reserve_margin = params["reserve_margin"]

    model = pyo.ConcreteModel()
    model.K = pyo.Set(initialize=(0, 1), ordered=True)
    model.T = pyo.Set(initialize=range(num_periods), ordered=True)

    model.base_cost = pyo.Param(model.K, initialize=base_cost)
    model.var_cost = pyo.Param(model.K, initialize=var_cost)
    model.startup_cost = pyo.Param(model.K, initialize=startup_cost)
    model.max_units = pyo.Param(
        model.K, initialize=max_units, within=pyo.NonNegativeIntegers
    )
    model.min_output = pyo.Param(model.K, initialize=min_output)
    model.max_output = pyo.Param(model.K, initialize=max_output)
    model.initial_startup_cap = pyo.Param(
        model.K, initialize=initial_startup_cap, within=pyo.NonNegativeIntegers
    )
    model.demand = pyo.Param(
        model.T, initialize={period: demand[period] for period in range(num_periods)}
    )
    model.reserve_margin = pyo.Param(initialize=reserve_margin)

    model.operating = pyo.Var(
        model.K,
        model.T,
        domain=pyo.NonNegativeIntegers,
        bounds=lambda mdl, kind, period: (0, mdl.max_units[kind]),
    )
    model.generation = pyo.Var(
        model.K, model.T, domain=pyo.NonNegativeReals
    )
    model.startups = pyo.Var(
        model.K, model.T, domain=pyo.NonNegativeIntegers
    )

    model.demand_requirement = pyo.Constraint(
        model.T,
        rule=lambda mdl, period: (
            sum(mdl.generation[kind, period] for kind in mdl.K)
            >= mdl.demand[period]
        ),
    )
    model.minimum_generation = pyo.Constraint(
        model.K,
        model.T,
        rule=lambda mdl, kind, period: (
            mdl.generation[kind, period]
            >= mdl.min_output[kind] * mdl.operating[kind, period]
        ),
    )
    model.maximum_generation = pyo.Constraint(
        model.K,
        model.T,
        rule=lambda mdl, kind, period: (
            mdl.generation[kind, period]
            <= mdl.max_output[kind] * mdl.operating[kind, period]
        ),
    )
    model.reserve_requirement = pyo.Constraint(
        model.T,
        rule=lambda mdl, period: (
            sum(
                mdl.max_output[kind] * mdl.operating[kind, period]
                for kind in mdl.K
            )
            >= (1 + mdl.reserve_margin) * mdl.demand[period]
        ),
    )

    model.initial_startup_balance = pyo.Constraint(
        model.K,
        rule=lambda mdl, kind: mdl.startups[kind, 0] == mdl.operating[kind, 0],
    )
    model.initial_startup_limit = pyo.Constraint(
        model.K,
        rule=lambda mdl, kind: (
            mdl.startups[kind, 0] <= mdl.initial_startup_cap[kind]
        ),
    )

    def startup_requirement_rule(mdl, kind, period):
        if period == 0:
            return pyo.Constraint.Skip
        return (
            mdl.startups[kind, period]
            >= mdl.operating[kind, period] - mdl.operating[kind, period - 1]
        )

    model.startup_requirement = pyo.Constraint(
        model.K, model.T, rule=startup_requirement_rule
    )

    def subsequent_startup_limit_rule(mdl, kind, period):
        if period == 0:
            return pyo.Constraint.Skip
        return mdl.startups[kind, period] <= mdl.operating[kind, period - 1]

    model.subsequent_startup_limit = pyo.Constraint(
        model.K, model.T, rule=subsequent_startup_limit_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.base_cost[kind] * model.operating[kind, period]
            + model.var_cost[kind] * model.generation[kind, period]
            + model.startup_cost[kind] * model.startups[kind, period]
            for kind in model.K
            for period in model.T
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when it cannot load a feasible solution.
        # Preserve unexpected RuntimeErrors for the calling harness.
        if "a feasible solution was not found" not in str(exc).lower():
            raise
        return {"objective": None, "status": "no_feasible_solution"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    base_cost_type0 = params["base_cost_type0"]
    base_cost_type1 = params["base_cost_type1"]
    var_cost_type0 = params["var_cost_type0"]
    var_cost_type1 = params["var_cost_type1"]
    startup_cost_type0 = params["startup_cost_type0"]
    startup_cost_type1 = params["startup_cost_type1"]
    max_units_type0 = params["max_units_type0"]
    max_units_type1 = params["max_units_type1"]
    demand = params["demand"]
    min_output_type0 = params["min_output_type0"]
    max_output_type0 = params["max_output_type0"]
    min_output_type1 = params["min_output_type1"]
    max_output_type1 = params["max_output_type1"]
    reserve_margin = params["reserve_margin"]
    max_startup_type0_period0 = params["max_startup_type0_period0"]
    max_startup_type1_period0 = params["max_startup_type1_period0"]
    num_periods = params["num_periods"]

    periods = range(num_periods)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Number of generators operational per period
    n0 = model.addVars(periods, vtype=GRB.INTEGER, lb=0, ub=max_units_type0, name="n0")
    n1 = model.addVars(periods, vtype=GRB.INTEGER, lb=0, ub=max_units_type1, name="n1")

    # Power output per period (continuous)
    p0 = model.addVars(periods, vtype=GRB.CONTINUOUS, lb=0.0, name="p0")
    p1 = model.addVars(periods, vtype=GRB.CONTINUOUS, lb=0.0, name="p1")

    # Startups per period
    s0 = model.addVars(periods, vtype=GRB.INTEGER, lb=0, name="s0")
    s1 = model.addVars(periods, vtype=GRB.INTEGER, lb=0, name="s1")

    # Objective
    model.setObjective(
        gp.quicksum(
            base_cost_type0 * n0[t]
            + base_cost_type1 * n1[t]
            + var_cost_type0 * p0[t]
            + var_cost_type1 * p1[t]
            + startup_cost_type0 * s0[t]
            + startup_cost_type1 * s1[t]
            for t in periods
        ),
        GRB.MINIMIZE
    )

    for t in periods:
        d = demand[t]

        # Demand satisfaction
        model.addConstr(p0[t] + p1[t] >= d, name=f"demand_{t}")

        # Output bounds based on number of units
        model.addConstr(p0[t] >= min_output_type0 * n0[t], name=f"min_p0_{t}")
        model.addConstr(p0[t] <= max_output_type0 * n0[t], name=f"max_p0_{t}")
        model.addConstr(p1[t] >= min_output_type1 * n1[t], name=f"min_p1_{t}")
        model.addConstr(p1[t] <= max_output_type1 * n1[t], name=f"max_p1_{t}")

        # Reserve margin: total max output >= demand * (1 + reserve_margin)
        model.addConstr(
            max_output_type0 * n0[t] + max_output_type1 * n1[t] >= d * (1 + reserve_margin),
            name=f"reserve_{t}"
        )

        # Startup constraints
        if t == 0:
            model.addConstr(s0[t] <= max_startup_type0_period0, name=f"startup0_p0")
            model.addConstr(s1[t] <= max_startup_type1_period0, name=f"startup1_p0")
        else:
            # Startups limited by units operational in previous period
            model.addConstr(s0[t] <= n0[t - 1], name=f"startup0_{t}")
            model.addConstr(s1[t] <= n1[t - 1], name=f"startup1_{t}")

        # Startups cannot exceed units operational this period
        model.addConstr(s0[t] <= n0[t], name=f"startup0_cap_{t}")
        model.addConstr(s1[t] <= n1[t], name=f"startup1_cap_{t}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}
```

### 6. Objective values

Rules that certify it: gate, panel_base_2of3, ind_gate.

#### param_screen

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 2927.0 (optimal) | 3880.9999999999995 (optimal) | 2927.0 (optimal) |
| 1 | 1918.0086925661913 (optimal) | 2765.2323235106874 (optimal) | 1918.0086925661913 (optimal) |
| 2 | 2897.7708830662004 (optimal) | 4374.747997089818 (optimal) | 2897.7708830662004 (optimal) |
| 3 | 1769.3623347393052 (optimal) | 2337.7216685328226 (optimal) | 1769.3623347393054 (optimal) |
| 4 | 3206.440923764657 (optimal) | 4075.120740773476 (optimal) | 3206.440923764657 (optimal) |
| 5 | 2433.0511234689543 (optimal) | 3256.8120606737243 (optimal) | 2433.0511234689543 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 2927.0 (optimal) | 3880.9999999999995 (optimal) | 2927.0 (optimal) |
| 1 | 1918.0086925661913 (optimal) | 2765.2323235106874 (optimal) | 1918.0086925661913 (optimal) |
| 2 | 2475.9663099721115 (optimal) | 3379.4884186937484 (optimal) | 2475.966309972111 (optimal) |
| 3 | 2127.645175761718 (optimal) | 2853.7535899035056 (optimal) | 2127.645175761718 (optimal) |
| 4 | 3458.8696071406775 (optimal) | 5120.539670774051 (optimal) | 3458.8696071406775 (optimal) |
| 5 | 3446.586143497119 (optimal) | 4223.452563386985 (optimal) | 3446.5861434971184 (optimal) |


## 7. sample_200 (stream (OptMATH-295))

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `sample_200` |
| Set | stream (OptMATH-295) |
| Source record | OptMATH-Train record 84975 |
| Optimization sense | not determined from the problem text (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 2.0 |
| Label | 4.0 |
| Rules that certify it | panel_base_2of3 (values: 2.0) |
| Label source | `artifacts/v2/optmath_295/problems.csv`, OptMATH-Train record 84975, field `answer`; the dataset stores no solution |

### 2. Certifying clique of panel_base_2of3 and values at instance 0

Families that agree at the stated instance (abs(a-b) <= 1e-4*max(1,|a|,|b|)): A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5). The third family: B (GPT-6.1 Sol) returns 5.999999999911182.

| Family | Program | Value at instance 0 | Status at instance 0 | In the certifying clique | Matches the label (round_aware) |
|---|---|---|---|---|---|
| A (DeepSeek-V4-Flash) | A-direct.py | 2.0 | optimal | yes | no |
| B (GPT-6.1 Sol) | B-structured.py | 5.999999999911182 | optimal | no | no |
| C (Claude Sonnet 5.5) | C-direct.py | 2.0 | optimal | yes | no |

### 3. Problem text

```
In a manufacturing facility, you are tasked with scheduling a set of jobs on multiple machines to minimize the total completion time, known as the *makespan*. Each job consists of a sequence of operations that must be performed in a specific order, and each operation is assigned to a particular machine. The goal is to determine the start times for each operation while respecting the constraints of machine availability and operation precedence.

There are three jobs, labeled Job 0, Job 1, and Job 2. Each job has two operations that must be performed in sequence:
- **Job 0**: Operation 0 must be completed before Operation 1 can begin.
- **Job 1**: Operation 0 must be completed before Operation 1 can begin.
- **Job 2**: Operation 0 must be completed before Operation 1 can begin.

Each operation has a processing time of 1 unit of time. Operations are assigned to specific machines, and each machine can only handle one operation at a time. The order in which operations are processed on the same machine is determined by binary decision variables, which indicate whether one operation starts before another.

The objective is to minimize the *makespan*, which is the total time taken to complete all jobs. The makespan is defined as the maximum completion time across all operations.

The constraints are as follows:
1. **Precedence Constraints**: For each job, the second operation cannot start until the first operation is completed. Specifically:
   - Operation 1 of Job 0 must start at least 1 unit of time after Operation 0 of Job 0.
   - Operation 1 of Job 1 must start at least 1 unit of time after Operation 0 of Job 1.
   - Operation 1 of Job 2 must start at least 1 unit of time after Operation 0 of Job 2.

2. **Machine Capacity Constraints**: For all pairs of operations assigned to the same machine, the following constraints ensure that no two operations overlap:
   - If Operation 0 of Job 0 starts before Operation 1 of Job 0, then Operation 1 of Job 0 must start at least 1 unit of time after Operation 0 of Job 0 completes.
   - Similarly, if Operation 0 of Job 0 starts before Operation 0 of Job 1, then Operation 0 of Job 1 must start at least 1 unit of time after Operation 0 of Job 0 completes.
   - These constraints apply to all pairs of operations that could potentially overlap on the same machine, using a large coefficient (100000) to enforce the order of operations.

3. **Makespan Definition**: The makespan must be at least as large as the completion time of every operation. Specifically:
   - The makespan must be at least 1 unit of time after the start of Operation 0 of Job 0.
   - The makespan must be at least 1 unit of time after the start of Operation 1 of Job 0.
   - The makespan must be at least 1 unit of time after the start of Operation 0 of Job 1.
   - The makespan must be at least 1 unit of time after the start of Operation 1 of Job 1.
   - The makespan must be at least 1 unit of time after the start of Operation 0 of Job 2.
   - The makespan must be at least 1 unit of time after the start of Operation 1 of Job 2.

4. **Non-Negativity Constraints**: All start times for operations must be non-negative.

5. **Binary Decision Variables**: The order of operations on the same machine is determined by binary variables, which take the value 0 or 1. These variables indicate whether one operation starts before another on the same machine.

Your task is to determine the start times for each operation on the machines such that:
- All operations are completed in the correct sequence for each job.
- No two operations overlap on the same machine.
- The total completion time (makespan) is minimized.

This problem involves balancing the sequencing of operations across jobs to ensure efficient use of the machines while minimizing the overall time required to complete all jobs.
```

### 4. spec.json (`spec` and `warnings`)

```json
"processing_time": {"base":1,"perturb":{"mode":"abs","lo":0.5,"hi":3.0,"integer":false}}
"big_M": {"base":100000,"perturb":{"mode":"abs","lo":10.0,"hi":100000.0,"integer":false}}
```

Warnings:

```
none
```

### 5. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    pt = params["processing_time"]
    big_M = params["big_M"]

    # Each job has 2 operations: (job, op)
    jobs = [0, 1, 2]
    ops = [0, 1]
    all_ops = [(j, o) for j in jobs for o in ops]

    # Machine assignment (structural). Standard job-shop 3x2 layout.
    # Assign so that each operation has a machine; operations on same machine must not overlap.
    # Job0: op0 -> M0, op1 -> M1
    # Job1: op0 -> M1, op1 -> M2
    # Job2: op0 -> M2, op1 -> M0
    machine_of = {
        (0, 0): 0, (0, 1): 1,
        (1, 0): 1, (1, 1): 2,
        (2, 0): 2, (2, 1): 0,
    }

    # Pairs of operations sharing the same machine (unordered pairs)
    machine_pairs = []
    for a in range(len(all_ops)):
        for b in range(a + 1, len(all_ops)):
            op_a = all_ops[a]
            op_b = all_ops[b]
            if machine_of[op_a] == machine_of[op_b]:
                machine_pairs.append((op_a, op_b))

    model = pyo.ConcreteModel()

    model.OPS = pyo.Set(initialize=all_ops, dimen=2)
    model.PAIRS = pyo.Set(initialize=machine_pairs, dimen=4)

    model.start = pyo.Var(model.OPS, domain=pyo.NonNegativeReals)
    model.makespan = pyo.Var(domain=pyo.NonNegativeReals)
    model.pairwise = pyo.Var(model.PAIRS, domain=pyo.Binary)

    # Precedence constraints: op1 starts at least pt after op0 completes
    def precedence_rule(m, j):
        return m.start[j, 1] >= m.start[j, 0] + pt
    model.precedence = pyo.Constraint(jobs, rule=precedence_rule)

    # Machine disjunctive constraints using big-M and binary ordering variable
    def machine_rule(m, a0, a1, b0, b1):
        return m.start[a0, a1] + pt <= m.start[b0, b1] + big_M * (1 - m.pairwise[a0, a1, b0, b1])

    def machine_rule2(m, a0, a1, b0, b1):
        return m.start[b0, b1] + pt <= m.start[a0, a1] + big_M * m.pairwise[a0, a1, b0, b1]

    model.machine_a = pyo.Constraint(model.PAIRS, rule=machine_rule)
    model.machine_b = pyo.Constraint(model.PAIRS, rule=machine_rule2)

    # Makespan definition
    def makespan_rule(m, j, o):
        return m.makespan >= m.start[j, o] + pt
    model.makespan_def = pyo.Constraint(model.OPS, rule=makespan_rule)

    model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"assumption":"Machine assignments are unspecified; assume all six operations share one machine.","sets":{"jobs":[0,1,2],"steps":[0,1],"operations":"jobs x steps","machine_pairs":"all unordered pairs of distinct operations"},"params":{"processing_time":"params['processing_time'], nonnegative","big_M":"params['big_M'], nonnegative"},"variables":{"start[j,k]":"nonnegative continuous","before[a,b]":"binary for each machine pair; 1 means a precedes b","makespan":"nonnegative continuous"},"constraints":["start[j,1] >= start[j,0] + processing_time for every job j","start[b] >= start[a] + processing_time - big_M*(1-before[a,b]) for every machine pair (a,b)","start[a] >= start[b] + processing_time - big_M*before[a,b] for every machine pair (a,b)","makespan >= start[j,k] + processing_time for every operation (j,k)"],"objective":"minimize makespan"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    jobs = range(3)
    steps = range(2)
    operations = [(job, step) for job in jobs for step in steps]
    machine_pairs = [
        (first[0], first[1], second[0], second[1])
        for first, second in combinations(operations, 2)
    ]

    model = pyo.ConcreteModel()

    model.jobs = pyo.Set(initialize=jobs, ordered=True)
    model.operations = pyo.Set(
        initialize=operations, dimen=2, ordered=True
    )
    model.machine_pairs = pyo.Set(
        initialize=machine_pairs, dimen=4, ordered=True
    )

    model.processing_time = pyo.Param(
        initialize=params["processing_time"],
        within=pyo.NonNegativeReals,
    )
    model.big_M = pyo.Param(
        initialize=params["big_M"],
        within=pyo.NonNegativeReals,
    )

    model.start = pyo.Var(
        model.operations, domain=pyo.NonNegativeReals
    )
    model.before = pyo.Var(
        model.machine_pairs, domain=pyo.Binary
    )
    model.makespan = pyo.Var(domain=pyo.NonNegativeReals)

    def precedence_rule(instance, job):
        return (
            instance.start[job, 1]
            >= instance.start[job, 0] + instance.processing_time
        )

    model.precedence = pyo.Constraint(
        model.jobs, rule=precedence_rule
    )

    def forward_order_rule(instance, job_a, step_a, job_b, step_b):
        return (
            instance.start[job_b, step_b]
            >= instance.start[job_a, step_a]
            + instance.processing_time
            - instance.big_M
            * (1 - instance.before[job_a, step_a, job_b, step_b])
        )

    model.forward_order = pyo.Constraint(
        model.machine_pairs, rule=forward_order_rule
    )

    def reverse_order_rule(instance, job_a, step_a, job_b, step_b):
        return (
            instance.start[job_a, step_a]
            >= instance.start[job_b, step_b]
            + instance.processing_time
            - instance.big_M
            * instance.before[job_a, step_a, job_b, step_b]
        )

    model.reverse_order = pyo.Constraint(
        model.machine_pairs, rule=reverse_order_rule
    )

    def completion_rule(instance, job, step):
        return (
            instance.makespan
            >= instance.start[job, step] + instance.processing_time
        )

    model.completion = pyo.Constraint(
        model.operations, rule=completion_rule
    )

    model.total_makespan = pyo.Objective(
        expr=model.makespan, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # Appsi can raise when no feasible solution is available to load.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_makespan))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    processing_time = params["processing_time"]
    big_M = params["big_M"]

    # Jobs: 0, 1, 2; Operations: 0, 1
    # Machine assignment (from problem structure):
    # Job 0 Op 0 -> Machine 0
    # Job 0 Op 1 -> Machine 1
    # Job 1 Op 0 -> Machine 0
    # Job 1 Op 1 -> Machine 2
    # Job 2 Op 0 -> Machine 1
    # Job 2 Op 1 -> Machine 2
    # (Classic 3-job 3-machine job shop routing)

    machine_assignment = {
        (0, 0): 0,
        (0, 1): 1,
        (1, 0): 0,
        (1, 1): 2,
        (2, 0): 1,
        (2, 1): 2,
    }

    model = gp.Model("jobshop")
    model.setParam("OutputFlag", 0)

    # Start time variables for each (job, operation)
    start = {}
    for j in range(3):
        for o in range(2):
            start[j, o] = model.addVar(lb=0.0, name=f"start_{j}_{o}")

    # Makespan variable
    makespan = model.addVar(lb=0.0, name="makespan")

    model.setObjective(makespan, GRB.MINIMIZE)

    # 1. Precedence constraints: op 1 starts after op 0 completes
    for j in range(3):
        model.addConstr(
            start[j, 1] >= start[j, 0] + processing_time,
            name=f"prec_{j}"
        )

    # 2. Machine capacity constraints
    # Collect all (job, op) pairs grouped by machine
    from collections import defaultdict
    machine_ops = defaultdict(list)
    for (j, o), mach in machine_assignment.items():
        machine_ops[mach].append((j, o))

    # For each machine, for each pair of operations, add disjunctive constraints
    order_vars = {}
    for mach, ops in machine_ops.items():
        for idx_a in range(len(ops)):
            for idx_b in range(idx_a + 1, len(ops)):
                ja, oa = ops[idx_a]
                jb, ob = ops[idx_b]
                # Binary: y=1 means (ja,oa) before (jb,ob); y=0 means (jb,ob) before (ja,oa)
                y = model.addVar(vtype=GRB.BINARY, name=f"order_{ja}_{oa}_{jb}_{ob}")
                order_vars[ja, oa, jb, ob] = y

                # If y=1: start[jb,ob] >= start[ja,oa] + processing_time
                model.addConstr(
                    start[jb, ob] >= start[ja, oa] + processing_time - big_M * (1 - y),
                    name=f"mach_{mach}_{ja}{oa}_{jb}{ob}_fwd"
                )
                # If y=0: start[ja,oa] >= start[jb,ob] + processing_time
                model.addConstr(
                    start[ja, oa] >= start[jb, ob] + processing_time - big_M * y,
                    name=f"mach_{mach}_{ja}{oa}_{jb}{ob}_bwd"
                )

    # 3. Makespan >= completion time of every operation
    for j in range(3):
        for o in range(2):
            model.addConstr(
                makespan >= start[j, o] + processing_time,
                name=f"mkspan_{j}_{o}"
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 6. Objective values

Rules that certify it: panel_base_2of3.

#### param_screen

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 2.0 (optimal) | 5.999999999911182 (optimal) | 2.0 (optimal) |
| 1 | 4.197133992289419 (optimal) | 12.591401976862214 (optimal) | 6.295700988433161 (optimal) |
| 2 | 2.3751465918455965 (optimal) | 7.125439775507942 (optimal) | 3.5627198877616766 (optimal) |
| 3 | 4.682356070820062 (optimal) | 14.047067531166249 (optimal) | 7.023534106198166 (optimal) |
| 4 | 5.460897838524227 (optimal) | 16.38269351213307 (optimal) | 8.191346757783514 (optimal) |
| 5 | 3.1096090984263522 (optimal) | 9.328827294908542 (optimal) | 4.664413647638699 (optimal) |

#### independent

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 2.0 (optimal) | 5.999999999911182 (optimal) | 2.0 (optimal) |
| 1 | 4.197133992289419 (optimal) | 12.591401976862214 (optimal) | 6.295700988433161 (optimal) |
| 2 | 2.3751465918455965 (optimal) | 7.125439775507942 (optimal) | 3.5627198877616766 (optimal) |
| 3 | 4.682356070820062 (optimal) | 14.047067531166249 (optimal) | 7.023534106198166 (optimal) |
| 4 | 5.460897838524227 (optimal) | 16.38269351213307 (optimal) | 8.191346757783514 (optimal) |
| 5 | 3.1096090984263522 (optimal) | 9.328827294908542 (optimal) | 4.664413647638699 (optimal) |


## 8. sample_220 (stream (OptMATH-295))

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `sample_220` |
| Set | stream (OptMATH-295) |
| Source record | OptMATH-Train record 172949 |
| Optimization sense | not determined from the problem text (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 28057.684210526317 |
| Label | 27737.0 |
| Rules that certify it | panel_base_2of3 (values: 28057.684210526317) |
| Label source | `artifacts/v2/optmath_295/problems.csv`, OptMATH-Train record 172949, field `answer`; the dataset stores no solution |

### 2. Certifying clique of panel_base_2of3 and values at instance 0

Families that agree at the stated instance (abs(a-b) <= 1e-4*max(1,|a|,|b|)): B (GPT-6.1 Sol) and C (Claude Sonnet 5.5). The third family: A (DeepSeek-V4-Flash) returns 28028.0.

| Family | Program | Value at instance 0 | Status at instance 0 | In the certifying clique | Matches the label (round_aware) |
|---|---|---|---|---|---|
| A (DeepSeek-V4-Flash) | A-direct.py | 28028.0 | optimal | no | no |
| B (GPT-6.1 Sol) | B-structured.py | 28057.684210526317 | optimal | yes | no |
| C (Claude Sonnet 5.5) | C-direct.py | 28057.684210526313 | optimal | yes | no |

### 3. Problem text

```
A supply chain network consists of five hubs with specific supply and demand requirements. Hub 0 has a demand of 345 units, Hub 1 has a demand of 655 units, Hub 2 has a supply of 774 units, Hub 3 has a supply of 142 units, and Hub 4 has a supply of 84 units. The goal is to minimize the total cost, which includes fixed costs for establishing connections between hubs and variable costs for shipping goods. Fixed costs for establishing connections range from 1901 to 2075 units, depending on the hub pair. Variable shipping costs range from 19 to 21 units per unit shipped, depending on the hub pair. Each connection has a maximum capacity limit, ranging from 539 to 990 units, depending on the hub pair. Decisions include determining which connections to establish (binary decision) and how much to ship along each established connection (continuous decision). Constraints include ensuring the flow of goods between hubs does not exceed the connection capacity, the total flow into a hub minus the total flow out equals the hub’s net demand, and connections can only be used if established. The objective is to minimize the total cost while meeting all demand and capacity constraints.
```

### 4. spec.json (`spec` and `warnings`)

```json
"demand_hub0": {"base":345,"perturb":{"mode":"rel","r":0.5}}
"demand_hub1": {"base":655,"perturb":{"mode":"rel","r":0.5}}
"supply_hub2": {"base":774,"perturb":{"mode":"rel","r":0.5}}
"supply_hub3": {"base":142,"perturb":{"mode":"rel","r":0.5}}
"supply_hub4": {"base":84,"perturb":{"mode":"rel","r":0.5}}
"fixed_cost_range": {"base":[1901,2075],"perturb":{"mode":"rel","r":0.5}}
"variable_cost_range": {"base":[19,21],"perturb":{"mode":"rel","r":0.5}}
"capacity_range": {"base":[539,990],"perturb":{"mode":"rel","r":0.4}}
```

Warnings:

```
none
```

### 5. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    n = 5
    hub_ids = list(range(n))
    net = {
        0: params["demand_hub0"],
        1: params["demand_hub1"],
        2: -params["supply_hub2"],
        3: -params["supply_hub3"],
        4: -params["supply_hub4"],
    }
    links = [(i, j) for i in hub_ids for j in hub_ids if i != j]

    def _val(spec, i, j):
        lo, hi = spec
        if hi == lo:
            return lo
        scaled = (i * n + j) % (hi - lo + 1)
        return lo + scaled

    fixed_cost = {}
    var_cost = {}
    cap = {}
    for (i, j) in links:
        fixed_cost[(i, j)] = _val(params["fixed_cost_range"], i, j)
        var_cost[(i, j)] = _val(params["variable_cost_range"], i, j)
        cap[(i, j)] = _val(params["capacity_range"], i, j)

    model = pyo.ConcreteModel()
    model.hubs = pyo.Set(initialize=hub_ids)
    model.links = pyo.Set(initialize=links, dimen=2)

    model.x = pyo.Var(model.links, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.links, domain=pyo.Binary)

    def flow_rule(md, i, j):
        return md.x[(i, j)] <= cap[(i, j)] * md.y[(i, j)]
    model.flow_cap = pyo.Constraint(model.links, rule=flow_rule)

    def balance_rule(md, k):
        return sum(md.x[(k, j)] for j in hub_ids if j != k) - \
               sum(md.x[(i, k)] for i in hub_ids if i != k) == net[k]
    model.balance = pyo.Constraint(model.hubs, rule=balance_rule)

    def obj_rule(md):
        return sum(fixed_cost[(i, j)] * md.y[(i, j)] +
                   var_cost[(i, j)] * md.x[(i, j)] for (i, j) in links)
    model.objective = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.objective))
    except Exception as e:
        return {"objective": None, "status": "solver failure: " + str(e)[:60]}

    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"H":[0,1,2,3,4],"A":"all ordered pairs (i,j) in H x H with i != j, lexicographically ordered"},"params":{"net_demand":"[params['demand_hub0'],params['demand_hub1'],-params['supply_hub2'],-params['supply_hub3'],-params['supply_hub4']]","fixed_cost":"interpolate params['fixed_cost_range'] by arc rank","variable_cost":"interpolate params['variable_cost_range'] by arc rank","capacity":"interpolate params['capacity_range'] by arc rank","interpolation":"lo + (hi-lo)*rank/(len(A)-1), with zero-based rank"},"variables":{"established[i,j]":"binary for (i,j) in A","flow[i,j]":"nonnegative continuous for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j]*established[i,j] for every arc","sum_i flow[i,h] - sum_j flow[h,j] = net_demand[h] for every hub"],"objective":"minimize sum_(i,j) fixed_cost[i,j]*established[i,j] + variable_cost[i,j]*flow[i,j]"}
#
# Modeling assumptions: connections are directed, and the stated supplies
# are net outflow requirements, consistent with the requested balance equalities.
# Ranges alone do not specify pair-specific data. This implementation assigns
# each range deterministically by linear interpolation over ordered arcs.
# This assignment is an explicit assumption, not supplied pair-specific data.

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand_hub0 = float(params["demand_hub0"])
    demand_hub1 = float(params["demand_hub1"])
    supply_hub2 = float(params["supply_hub2"])
    supply_hub3 = float(params["supply_hub3"])
    supply_hub4 = float(params["supply_hub4"])

    fixed_cost_range = tuple(float(v) for v in params["fixed_cost_range"])
    variable_cost_range = tuple(float(v) for v in params["variable_cost_range"])
    capacity_range = tuple(float(v) for v in params["capacity_range"])

    hub_quantities = (
        demand_hub0,
        demand_hub1,
        supply_hub2,
        supply_hub3,
        supply_hub4,
    )
    ranges = (fixed_cost_range, variable_cost_range, capacity_range)

    if any(not math.isfinite(v) or v < 0 for v in hub_quantities):
        return {"objective": None, "status": "invalid_parameters"}

    for bounds in ranges:
        if (
            len(bounds) != 2
            or any(not math.isfinite(v) or v < 0 for v in bounds)
            or bounds[0] > bounds[1]
        ):
            return {"objective": None, "status": "invalid_parameters"}

    hubs = tuple(range(5))
    arcs = tuple(
        (source, destination)
        for source in hubs
        for destination in hubs
        if source != destination
    )

    net_demand = {
        0: demand_hub0,
        1: demand_hub1,
        2: -supply_hub2,
        3: -supply_hub3,
        4: -supply_hub4,
    }

    def interpolate(bounds):
        lower, upper = bounds
        return {
            arc: lower + (upper - lower) * rank / (len(arcs) - 1)
            for rank, arc in enumerate(arcs)
        }

    model = pyo.ConcreteModel()

    model.hubs = pyo.Set(initialize=hubs, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.net_demand = pyo.Param(
        model.hubs, initialize=net_demand, within=pyo.Reals
    )
    model.fixed_cost = pyo.Param(
        model.arcs,
        initialize=interpolate(fixed_cost_range),
        within=pyo.NonNegativeReals,
    )
    model.variable_cost = pyo.Param(
        model.arcs,
        initialize=interpolate(variable_cost_range),
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.arcs,
        initialize=interpolate(capacity_range),
        within=pyo.NonNegativeReals,
    )

    model.established = pyo.Var(model.arcs, domain=pyo.Binary)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, source, destination):
        return (
            network.flow[source, destination]
            <= network.capacity[source, destination]
            * network.established[source, destination]
        )

    model.connection_capacity = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def balance_rule(network, hub):
        inflow = sum(
            network.flow[source, hub]
            for source in network.hubs
            if source != hub
        )
        outflow = sum(
            network.flow[hub, destination]
            for destination in network.hubs
            if destination != hub
        )
        return inflow - outflow == network.net_demand[hub]

    model.flow_balance = pyo.Constraint(model.hubs, rule=balance_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[source, destination]
            * model.established[source, destination]
            + model.variable_cost[source, destination]
            * model.flow[source, destination]
            for source, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when automatic solution loading finds no solution.
        # Re-raise unrelated exceptions so unexpected errors remain visible.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand_hub0 = params["demand_hub0"]
    demand_hub1 = params["demand_hub1"]
    supply_hub2 = params["supply_hub2"]
    supply_hub3 = params["supply_hub3"]
    supply_hub4 = params["supply_hub4"]
    fixed_cost_range = params["fixed_cost_range"]
    variable_cost_range = params["variable_cost_range"]
    capacity_range = params["capacity_range"]

    # Five hubs: 0,1 are demand hubs; 2,3,4 are supply hubs
    # Net balance: positive = net inflow required (demand), negative = net outflow available (supply)
    net_demand = {
        0:  demand_hub0,
        1:  demand_hub1,
        2: -supply_hub2,
        3: -supply_hub3,
        4: -supply_hub4,
    }

    hubs = list(range(5))

    # All directed arcs between distinct hubs
    arcs = [(i, j) for i in hubs for j in hubs if i != j]

    # Distribute fixed costs, variable costs, and capacities across arcs
    # using a simple linear interpolation so that the first arc gets the min
    # value and the last gets the max value.
    n_arcs = len(arcs)

    fc_min, fc_max = fixed_cost_range[0], fixed_cost_range[1]
    vc_min, vc_max = variable_cost_range[0], variable_cost_range[1]
    cap_min, cap_max = capacity_range[0], capacity_range[1]

    fixed_cost = {}
    variable_cost = {}
    capacity = {}

    for idx, arc in enumerate(arcs):
        t = idx / (n_arcs - 1) if n_arcs > 1 else 0.0
        fixed_cost[arc]    = fc_min  + t * (fc_max  - fc_min)
        variable_cost[arc] = vc_min  + t * (vc_max  - vc_min)
        capacity[arc]      = cap_min + t * (cap_max  - cap_min)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: whether arc (i,j) is established
    establish = model.addVars(arcs, vtype=GRB.BINARY, name="establish")

    # Continuous: flow on arc (i,j)
    flow = model.addVars(arcs, lb=0.0, vtype=GRB.CONTINUOUS, name="flow")

    # Objective: minimize total fixed + variable cost
    model.setObjective(
        gp.quicksum(fixed_cost[a] * establish[a] + variable_cost[a] * flow[a] for a in arcs),
        GRB.MINIMIZE
    )

    # Capacity constraints: flow <= capacity * establish
    for a in arcs:
        model.addConstr(flow[a] <= capacity[a] * establish[a], name=f"cap_{a[0]}_{a[1]}")

    # Flow balance: inflow - outflow == net_demand[i]
    for i in hubs:
        inflow  = gp.quicksum(flow[(j, i)] for j in hubs if j != i)
        outflow = gp.quicksum(flow[(i, j)] for j in hubs if j != i)
        model.addConstr(inflow - outflow == net_demand[i], name=f"balance_{i}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}
```

### 6. Objective values

Rules that certify it: panel_base_2of3.

#### param_screen

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 28028.0 (optimal) | 28057.684210526317 (optimal) | 28057.684210526313 (optimal) |
| 1 | 24790.589268348132 (optimal) | none (invalid_parameters) | 26042.480730277646 (optimal) |
| 2 | 29395.12711250315 (optimal) | none (invalid_parameters) | 29659.515776842833 (optimal) |
| 3 | 26030.758867493078 (optimal) | none (invalid_parameters) | 25435.952727533004 (optimal) |
| 4 | 24001.7795134761 (optimal) | 25109.118782226607 (optimal) | 25109.118782226607 (optimal) |
| 5 | 25476.23048999746 (optimal) | none (invalid_parameters) | 27676.16516847034 (optimal) |

#### independent

Decision: UNINFORMATIVE; clique none; informative instances [0]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 28028.0 (optimal) | 28057.684210526317 (optimal) | 28057.684210526313 (optimal) |
| 1 | none (solver failure: A feasible solution was not found, so no solution can be loa) | none (no_solution) | none (infeasible) |
| 2 | none (solver failure: A feasible solution was not found, so no solution can be loa) | none (invalid_parameters) | none (infeasible) |
| 3 | none (solver failure: A feasible solution was not found, so no solution can be loa) | none (no_solution) | none (infeasible) |
| 4 | none (solver failure: A feasible solution was not found, so no solution can be loa) | none (invalid_parameters) | none (infeasible) |
| 5 | none (solver failure: A feasible solution was not found, so no solution can be loa) | none (no_solution) | none (infeasible) |


## 9. sample_243 (stream (OptMATH-295))

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `sample_243` |
| Set | stream (OptMATH-295) |
| Source record | OptMATH-Train record 31720 |
| Optimization sense | not determined from the problem text (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 0.013513534831648254 |
| Label | 0.012070001450990001 |
| Rules that certify it | gate, panel_base_2of3, ind_gate (values: 0.013513534831648254) |
| Label source | `artifacts/v2/optmath_295/problems.csv`, OptMATH-Train record 31720, field `answer`; the dataset stores no solution |

### 2. Certifying clique of panel_base_2of3 and values at instance 0

Families that agree at the stated instance (abs(a-b) <= 1e-4*max(1,|a|,|b|)): B (GPT-6.1 Sol) and C (Claude Sonnet 5.5). The third family: A (DeepSeek-V4-Flash) returns none.

| Family | Program | Value at instance 0 | Status at instance 0 | In the certifying clique | Matches the label (round_aware) |
|---|---|---|---|---|---|
| A (DeepSeek-V4-Flash) | A-direct.py | none | crash:File "<PATH>/highs.py", line 620, in _set_objective \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Highs | no | no |
| B (GPT-6.1 Sol) | B-structured.py | 0.013513534831648254 | optimal | yes | no |
| C (Claude Sonnet 5.5) | C-direct.py | 0.013513574228545884 | optimal | yes | no |

### 3. Problem text

```
The problem involves optimizing a portfolio of 10 assets to minimize the overall risk, measured by portfolio variance, while ensuring the portfolio achieves a minimum expected return of 10%. Each asset has a specific expected return and a maximum allocation limit of 30%. The total allocation across all assets must sum to 100%. The portfolio variance is determined by the weighted contributions of each asset and their interactions, as defined by the covariance between the assets. For example, Asset 0 and Asset 1 have a covariance of 0.0758, indicating their returns tend to move together, while Asset 0 and Asset 2 have a covariance of -0.0093, suggesting their returns move in opposite directions. The quadratic constraint explicitly defines the portfolio variance in terms of the weights of the assets and their covariances. The objective is to minimize this variance while ensuring the weighted average return of the portfolio meets or exceeds 10%, and all allocation constraints are satisfied.
```

### 4. spec.json (`spec` and `warnings`)

```json
"target_return": {"base":0.1,"perturb":{"mode":"abs","lo":0.05,"hi":0.18,"integer":false}}
"max_allocation": {"base":0.3,"perturb":{"mode":"abs","lo":0.15,"hi":0.5,"integer":false}}
"total_allocation": {"base":1.0,"perturb":{"mode":"abs","lo":1.0,"hi":1.0,"integer":false}}
"expected_returns": {"base":[0.12,0.1,0.08,0.14,0.11,0.09,0.13,0.07,0.15,0.06],"perturb":{"mode":"rel","r":0.3}}
"covariance_matrix": {"base":[[0.04,0.0758,-0.0093,0.018,0.022,0.01,0.03,0.005,0.025,0.012],[0.0758,0.05,0.014,0.02,0.035,0.008,0.028,0.006,0.031,0.015],[-0.0093,0.014,0.03,0.01,0.005,0.012,-0.004,0.018,0.007,0.009],[0.018,0.02,0.01,0.045,0.025,0.015,0.022,0.011,0.019,0.013],[0.022,0.035,0.005,0.025,0.055,0.018,0.026,0.009,0.033,0.014],[0.01,0.008,0.012,0.015,0.018,0.035,0.011,0.017,0.012,0.02],[0.03,0.028,-0.004,0.022,0.026,0.011,0.06,0.007,0.024,0.016],[0.005,0.006,0.018,0.011,0.009,0.017,0.007,0.025,0.015,0.021],[0.025,0.031,0.007,0.019,0.033,0.012,0.024,0.015,0.07,0.019],[0.012,0.015,0.009,0.013,0.014,0.02,0.016,0.021,0.019,0.038]],"perturb":{"mode":"rel","r":0.25}}
"asset_count": {"base":10,"perturb":{"mode":"abs","lo":10.0,"hi":10.0,"integer":true}}
```

Warnings:

```
[total_allocation] degenerate abs range (lo == hi); perturbation has no effect
[asset_count] degenerate abs range (lo == hi); perturbation has no effect
```

### 5. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["asset_count"])
    target_return = params["target_return"]
    max_allocation = params["max_allocation"]
    total_allocation = params["total_allocation"]
    expected_returns = params["expected_returns"]
    covariance_matrix = params["covariance_matrix"]

    model = pyo.ConcreteModel()

    model.assets = pyo.RangeSet(0, n - 1)

    model.w = pyo.Var(model.assets, bounds=(0, max_allocation))

    def return_rule(m):
        return sum(expected_returns[i] * m.w[i] for i in m.assets) >= target_return

    model.return_con = pyo.Constraint(rule=return_rule)

    def budget_rule(m):
        return sum(m.w[i] for i in m.assets) == total_allocation

    model.budget_con = pyo.Constraint(rule=budget_rule)

    def obj_rule(m):
        return sum(
            covariance_matrix[i][j] * m.w[i] * m.w[j]
            for i in m.assets
            for j in m.assets
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
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
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB


def solve(params):
    target_return = params["target_return"]
    max_allocation = params["max_allocation"]
    total_allocation = params["total_allocation"]
    expected_returns = params["expected_returns"]
    covariance_matrix = params["covariance_matrix"]
    asset_count = params["asset_count"]

    model = gp.Model("portfolio")
    model.Params.OutputFlag = 0

    # Decision variables: portfolio weights, long-only with per-asset cap.
    w = model.addVars(
        asset_count,
        lb=0.0,
        ub=max_allocation,
        name="w",
    )

    # Full allocation constraint: weights must sum to total_allocation.
    model.addConstr(
        gp.quicksum(w[i] for i in range(asset_count)) == total_allocation,
        name="total_allocation",
    )

    # Minimum expected return constraint: weighted average return >= target_return.
    model.addConstr(
        gp.quicksum(expected_returns[i] * w[i] for i in range(asset_count))
        >= target_return,
        name="target_return",
    )

    # Objective: minimize portfolio variance w^T Sigma w.
    variance = gp.quicksum(
        covariance_matrix[i][j] * w[i] * w[j]
        for i in range(asset_count)
        for j in range(asset_count)
    )
    model.setObjective(variance, GRB.MINIMIZE)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    if model.status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD):
        return {"objective": None, "status": "infeasible"}

    return {"objective": None, "status": f"status_{model.status}"}
```

### 6. Objective values

Rules that certify it: gate, panel_base_2of3, ind_gate.

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:File "<PATH>/highs.py", line 620, in _set_objective \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Highs) | 0.013513534831648254 (optimal) | 0.013513574228545884 (optimal) |
| 1 | none (crash:File "<PATH>/highs.py", line 620, in _set_objective \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Highs) | 0.013085496305593169 (optimal) | 0.013085497922901016 (optimal) |
| 2 | none (crash:File "<PATH>/highs.py", line 620, in _set_objective \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Highs) | 0.014167053765242297 (optimal) | 0.014167111216944072 (optimal) |
| 3 | none (crash:File "<PATH>/highs.py", line 620, in _set_objective \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Highs) | 0.013348206655616243 (optimal) | 0.01334821331371761 (optimal) |
| 4 | none (crash:File "<PATH>/highs.py", line 620, in _set_objective \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Highs) | 0.010876028595983508 (optimal) | 0.010876035287212524 (optimal) |
| 5 | none (crash:File "<PATH>/highs.py", line 620, in _set_objective \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Highs) | 0.011421431226466206 (optimal) | 0.011421438983352138 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 3, 4]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:File "<PATH>/highs.py", line 620, in _set_objective \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Highs) | 0.013513534831648254 (optimal) | 0.013513574228545884 (optimal) |
| 1 | none (crash:File "<PATH>/highs.py", line 620, in _set_objective \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Highs) | none (infeasible_or_solver_failed) | none (infeasible) |
| 2 | none (crash:File "<PATH>/highs.py", line 620, in _set_objective \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Highs) | none (infeasible_or_solver_failed) | none (infeasible) |
| 3 | none (crash:File "<PATH>/highs.py", line 620, in _set_objective \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Highs) | 0.010617210095105205 (optimal) | 0.010617273967026272 (optimal) |
| 4 | none (crash:File "<PATH>/highs.py", line 620, in _set_objective \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Highs) | 0.013323033038882102 (optimal) | 0.013323037879141644 (optimal) |
| 5 | none (crash:File "<PATH>/highs.py", line 620, in _set_objective \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Highs) | none (infeasible_or_solver_failed) | none (infeasible) |


## 10. sample_290 (stream (OptMATH-295))

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `sample_290` |
| Set | stream (OptMATH-295) |
| Source record | OptMATH-Train record 176518 |
| Optimization sense | not determined from the problem text (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 811608.0 |
| Label | 800200.0 |
| Rules that certify it | gate, panel_base_2of3, ind_gate (values: 811608.0) |
| Label source | `artifacts/v2/optmath_295/problems.csv`, OptMATH-Train record 176518, field `answer`; the dataset stores no solution |

### 2. Certifying clique of panel_base_2of3 and values at instance 0

Families that agree at the stated instance (abs(a-b) <= 1e-4*max(1,|a|,|b|)): A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol). The third family: C (Claude Sonnet 5.5) returns 508313.0.

| Family | Program | Value at instance 0 | Status at instance 0 | In the certifying clique | Matches the label (round_aware) |
|---|---|---|---|---|---|
| A (DeepSeek-V4-Flash) | A-direct.py | 811608.0 | optimal | yes | no |
| B (GPT-6.1 Sol) | B-structured.py | 811608.0 | optimal | yes | no |
| C (Claude Sonnet 5.5) | C-direct.py | 508313.0 | optimal | no | no |

### 3. Problem text

```
Imagine you are managing a network of six distribution centers (facilities) that supply products to twelve retail stores (customers) across a region. Each distribution center has a fixed cost to operate, and each store has a specific demand that must be met. Your goal is to determine which distribution centers to open and how much product to ship from each open center to each store, while minimizing the total cost of operations and transportation.

#### Key Details:
1. **Distribution Centers (Facilities):**
   - There are six potential distribution centers, labeled as Facility 0 to Facility 5.
   - Each facility has a fixed operating cost:
     - Facility 0: $102,829
     - Facility 1: $100,573
     - Facility 2: $101,725
     - Facility 3: $99,989
     - Facility 4: $103,197
     - Facility 5: $104,176
   - Each facility has a maximum capacity for shipping products:
     - Facility 0: 1,035 units
     - Facility 1: 1,021 units
     - Facility 2: 959 units
     - Facility 3: 1,006 units
     - Facility 4: 1,011 units
     - Facility 5: 998 units

2. **Retail Stores (Customers):**
   - There are twelve retail stores, labeled as Customer 0 to Customer 11.
   - Each store has a specific demand for products:
     - Customer 0: 422 units
     - Customer 1: 378 units
     - Customer 2: 389 units
     - Customer 3: 408 units
     - Customer 4: 420 units
     - Customer 5: 380 units
     - Customer 6: 381 units
     - Customer 7: 384 units
     - Customer 8: 385 units
     - Customer 9: 390 units
     - Customer 10: 397 units
     - Customer 11: 393 units

3. **Transportation Costs:**
   - The cost to ship products from a distribution center to a retail store varies. For example:
     - Shipping from Facility 0 to Customer 0 costs $66 per unit.
     - Shipping from Facility 1 to Customer 1 costs $63 per unit.
     - Shipping from Facility 2 to Customer 2 costs $61 per unit.
     - Shipping from Facility 3 to Customer 3 costs $70 per unit.
     - Shipping from Facility 4 to Customer 4 costs $64 per unit.
     - Shipping from Facility 5 to Customer 5 costs $63 per unit.
   - Similar costs apply for all other combinations of facilities and customers.

#### Constraints:
1. **Demand Satisfaction:**
   - The total amount of product shipped to each retail store must exactly match its demand. For example:
     - Customer 0 must receive exactly 422 units from one or more distribution centers.
     - Customer 1 must receive exactly 378 units, and so on for all customers.

2. **Facility Capacity:**
   - The total amount of product shipped from a distribution center cannot exceed its capacity. For example:
     - Facility 0 cannot ship more than 1,035 units in total.
     - Facility 1 cannot ship more than 1,021 units, and so on for all facilities.

3. **Facility Opening:**
   - A distribution center can only ship products if it is open. For example:
     - If Facility 0 is open, it can ship up to 1,035 units.
     - If Facility 0 is closed, it cannot ship any products.

#### Objective:
Your task is to decide which distribution centers to open and how much product to ship from each open center to each retail store, while minimizing the total cost. The total cost includes:
- The fixed costs of opening the selected distribution centers.
- The variable transportation costs of shipping products from the open centers to the retail stores.

#### Example:
- If you decide to open Facility 0 and Facility 1, you incur their fixed costs ($102,829 + $100,573 = $203,402).
- If you ship 422 units from Facility 0 to Customer 0, the transportation cost is $66 × 422 = $27,852.
- If you ship 378 units from Facility 1 to Customer 1, the transportation cost is $63 × 378 = $23,814.
- The total cost would include these transportation costs plus the fixed costs of opening the facilities.

Your goal is to find the combination of open facilities and shipping quantities that satisfies all customer demands, respects facility capacities, and results in the lowest possible total cost.
```

### 4. spec.json (`spec` and `warnings`)

```json
"fixed_cost": {"base":[102829,100573,101725,99989,103197,104176],"perturb":{"mode":"rel","r":0.25}}
"capacity": {"base":[1035,1021,959,1006,1011,998],"perturb":{"mode":"rel","r":0.2}}
"demand": {"base":[422,378,389,408,420,380,381,384,385,390,397,393],"perturb":{"mode":"rel","r":0.1}}
"transport_cost_00": {"base":66,"perturb":{"mode":"rel","r":0.4}}
"transport_cost_11": {"base":63,"perturb":{"mode":"rel","r":0.4}}
"transport_cost_22": {"base":61,"perturb":{"mode":"rel","r":0.4}}
"transport_cost_33": {"base":70,"perturb":{"mode":"rel","r":0.4}}
"transport_cost_44": {"base":64,"perturb":{"mode":"rel","r":0.4}}
"transport_cost_55": {"base":63,"perturb":{"mode":"rel","r":0.4}}
```

Warnings:

```
none
```

### 5. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_fac = 6
    n_cust = 12
    facs = list(range(n_fac))
    custs = list(range(n_cust))

    fixed_cost = {i: params[f"fixed_cost"] if not isinstance(params.get("fixed_cost"), (list, tuple))
                  else params["fixed_cost"][i] for i in facs}
    capacity = {i: params[f"capacity"] if not isinstance(params.get("capacity"), (list, tuple))
                else params["capacity"][i] for i in facs}
    demand = {j: params[f"demand"] if not isinstance(params.get("demand"), (list, tuple))
              else params["demand"][j] for j in custs}

    # Handle scalar-or-list params cleanly
    if isinstance(params["fixed_cost"], (list, tuple)):
        fixed_cost = {i: params["fixed_cost"][i] for i in facs}
    else:
        fixed_cost = {i: params["fixed_cost"] for i in facs}

    if isinstance(params["capacity"], (list, tuple)):
        capacity = {i: params["capacity"][i] for i in facs}
    else:
        capacity = {i: params["capacity"] for i in facs}

    if isinstance(params["demand"], (list, tuple)):
        demand = {j: params["demand"][j] for j in custs}
    else:
        demand = {j: params["demand"] for j in custs}

    # Diagonal transportation costs are given; off-diagonal assumed via symmetric/indexed fallback.
    # Only specified params exist, so build a full cost matrix with a default for unspecified pairs.
    transport = {}
    specified = {
        (0, 0): params["transport_cost_00"],
        (1, 1): params["transport_cost_11"],
        (2, 2): params["transport_cost_22"],
        (3, 3): params["transport_cost_33"],
        (4, 4): params["transport_cost_44"],
        (5, 5): params["transport_cost_55"],
    }
    for i in facs:
        for j in custs:
            if (i, j) in specified:
                transport[(i, j)] = specified[(i, j)]
            else:
                # Fill unspecified pairs using the nearest specified diagonal per row/column
                transport[(i, j)] = specified.get((i, i), specified[(0, 0)])

    model = pyo.ConcreteModel()

    model.FAC = pyo.Set(initialize=facs)
    model.CUST = pyo.Set(initialize=custs)
    model.LINK = pyo.Set(initialize=[(i, j) for i in facs for j in custs])

    model.y = pyo.Var(model.FAC, within=pyo.Binary)
    model.x = pyo.Var(model.LINK, within=pyo.NonNegativeReals)

    model.fixed_cost_c = pyo.Param(model.FAC, initialize=fixed_cost)
    model.capacity_c = pyo.Param(model.FAC, initialize=capacity)
    model.demand_c = pyo.Param(model.CUST, initialize=demand)
    model.tcost_c = pyo.Param(model.LINK, initialize=transport)

    def objective_rule(m):
        return (sum(m.fixed_cost_c[i] * m.y[i] for i in m.FAC)
                + sum(m.tcost_c[(i, j)] * m.x[(i, j)] for (i, j) in m.LINK))
    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[(i, j)] for i in m.FAC) == m.demand_c[j]
    model.demand_con = pyo.Constraint(model.CUST, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.x[(i, j)] for j in m.CUST) <= m.capacity_c[i] * m.y[i]
    model.capacity_con = pyo.Constraint(model.FAC, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"F":"0..5","C":"0..11"},"params":{"fixed_cost":"F-indexed","capacity":"F-indexed nonnegative","demand":"C-indexed nonnegative","transport_cost_00":"scalar","transport_cost_11":"scalar","transport_cost_22":"scalar","transport_cost_33":"scalar","transport_cost_44":"scalar","transport_cost_55":"scalar"},"assumption":"Unspecified route costs equal the supplied cost for their originating facility: c[i,j]=transport_cost_ii for every j. The supplied data do not uniquely determine other route costs.","variables":{"opened[i]":"Binary","shipped[i,j]":"NonNegativeReals"},"constraints":["sum(i in F, shipped[i,j]) == demand[j] for each j in C","sum(j in C, shipped[i,j]) <= capacity[i]*opened[i] for each i in F"],"objective":"minimize sum(i in F, fixed_cost[i]*opened[i]) + sum(i in F,j in C, transport_cost_ii*shipped[i,j])"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    facilities = range(6)
    customers = range(12)

    fixed_cost = params["fixed_cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    facility_transport_cost = (
        params["transport_cost_00"],
        params["transport_cost_11"],
        params["transport_cost_22"],
        params["transport_cost_33"],
        params["transport_cost_44"],
        params["transport_cost_55"],
    )

    model = pyo.ConcreteModel()
    model.facilities = pyo.Set(initialize=facilities, ordered=True)
    model.customers = pyo.Set(initialize=customers, ordered=True)

    model.operating_cost = pyo.Param(
        model.facilities,
        initialize={i: float(fixed_cost[i]) for i in facilities},
        within=pyo.Reals,
    )
    model.shipping_capacity = pyo.Param(
        model.facilities,
        initialize={i: float(capacity[i]) for i in facilities},
        within=pyo.NonNegativeReals,
    )
    model.customer_demand = pyo.Param(
        model.customers,
        initialize={j: float(demand[j]) for j in customers},
        within=pyo.NonNegativeReals,
    )
    model.unit_transport_cost = pyo.Param(
        model.facilities,
        initialize={
            i: float(facility_transport_cost[i]) for i in facilities
        },
        within=pyo.Reals,
    )

    model.opened = pyo.Var(model.facilities, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.facilities,
        model.customers,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(instance, j):
        return (
            sum(instance.shipped[i, j] for i in instance.facilities)
            == instance.customer_demand[j]
        )

    model.demand_balance = pyo.Constraint(
        model.customers,
        rule=demand_rule,
    )

    def capacity_rule(instance, i):
        return (
            sum(instance.shipped[i, j] for j in instance.customers)
            <= instance.shipping_capacity[i] * instance.opened[i]
        )

    model.facility_capacity = pyo.Constraint(
        model.facilities,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.operating_cost[i] * model.opened[i]
                for i in model.facilities
            )
            + sum(
                model.unit_transport_cost[i] * model.shipped[i, j]
                for i in model.facilities
                for j in model.customers
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Continue to objective retrieval only for the expected
        # APPsi failure to load a feasible solution.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    capacity = params["capacity"]
    demand = params["demand"]

    n_facilities = 6
    n_customers = 12

    # Transport costs: only diagonal entries are specified; others must default to something.
    # The problem only names transport_cost_ij for i==j (0..5), so we build a full cost matrix.
    # For unspecified pairs we use 0 as a placeholder — the problem statement implies only
    # diagonal costs are given, so we set all others to 0 (they will still be decision variables
    # but with zero cost, letting the solver use them freely to satisfy demands).
    transport_cost = [[0.0] * n_customers for _ in range(n_facilities)]
    for i in range(n_facilities):
        key = f"transport_cost_{i}{i}"
        transport_cost[i][i] = params[key]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: open facility i
    open_fac = model.addVars(n_facilities, vtype=GRB.BINARY, name="open")

    # Continuous: units shipped from facility i to customer j
    ship = model.addVars(n_facilities, n_customers, lb=0.0, name="ship")

    # Objective: fixed costs + transportation costs
    model.setObjective(
        gp.quicksum(fixed_cost[i] * open_fac[i] for i in range(n_facilities)) +
        gp.quicksum(transport_cost[i][j] * ship[i, j]
                    for i in range(n_facilities)
                    for j in range(n_customers)),
        GRB.MINIMIZE
    )

    # Demand satisfaction: each customer's demand must be exactly met
    for j in range(n_customers):
        model.addConstr(
            gp.quicksum(ship[i, j] for i in range(n_facilities)) == demand[j],
            name=f"demand_{j}"
        )

    # Capacity: total shipped from facility i <= capacity[i] * open[i]
    for i in range(n_facilities):
        model.addConstr(
            gp.quicksum(ship[i, j] for j in range(n_customers)) <= capacity[i] * open_fac[i],
            name=f"capacity_{i}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 6. Objective values

Rules that certify it: gate, panel_base_2of3, ind_gate.

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 811608.0 (optimal) | 811608.0 (optimal) | 508313.0 (optimal) |
| 1 | 762954.7041457907 (optimal) | 762954.7041457907 (optimal) | 476498.42332663276 (optimal) |
| 2 | 794447.9397214035 (optimal) | 794447.9397214035 (optimal) | 538129.153863604 (optimal) |
| 3 | 860899.686553399 (optimal) | 860899.686553399 (optimal) | 581277.8300216912 (optimal) |
| 4 | 774264.8223562866 (optimal) | 774264.8223562866 (optimal) | 464524.0167901175 (optimal) |
| 5 | 766624.4777614692 (optimal) | 766624.4777614692 (optimal) | 492400.28921163623 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 811608.0 (optimal) | 811608.0 (optimal) | 508313.0 (optimal) |
| 1 | 762954.7041457907 (optimal) | 762954.7041457907 (optimal) | 476498.42332663276 (optimal) |
| 2 | 794447.9397214035 (optimal) | 794447.9397214035 (optimal) | 538129.153863604 (optimal) |
| 3 | 860899.686553399 (optimal) | 860899.686553399 (optimal) | 581277.8300216912 (optimal) |
| 4 | 774264.8223562866 (optimal) | 774264.8223562866 (optimal) | 464524.0167901175 (optimal) |
| 5 | 766624.4777614692 (optimal) | 766624.4777614692 (optimal) | 492400.28921163623 (optimal) |


## 11. conf_16675 (confirm (OptMATH-200))

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `conf_16675` |
| Set | confirm (OptMATH-200) |
| Source record | OptMATH-Train record 16675 |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 1235.5699207670264 |
| Label | 2347.1979356914976 |
| Rules that certify it | gate, panel_base_2of3, ind_gate (values: 1235.5699207670264) |
| Label source | `artifacts/v2/optmath_200/problems.csv`, OptMATH-Train record 16675, field `answer`; the dataset stores no solution |

### 2. Certifying clique of panel_base_2of3 and values at instance 0

Families that agree at the stated instance (abs(a-b) <= 1e-4*max(1,|a|,|b|)): B (GPT-6.1 Sol) and C (Claude Sonnet 5.5). The third family: A (DeepSeek-V4-Flash) returns 2360.897154905569.

| Family | Program | Value at instance 0 | Status at instance 0 | In the certifying clique | Matches the label (round_aware) |
|---|---|---|---|---|---|
| A (DeepSeek-V4-Flash) | A-direct.py | 2360.897154905569 | optimal | no | no |
| B (GPT-6.1 Sol) | B-structured.py | 1235.5699207670264 | optimal | yes | no |
| C (Claude Sonnet 5.5) | C-direct.py | 1235.5699207670268 | optimal | yes | no |

### 3. Problem text

```
The problem involves managing production planning for a manufacturing facility that produces three distinct items (Item 0, Item 1, and Item 2) over five time periods (Period 0 to Period 4). The facility operates a single machine that can produce only one item at a time. The goal is to minimize the total costs associated with production, inventory, and backlogs while meeting customer demand for each item in each period.

Key decisions include determining whether to produce each item on the machine in each period, with a production cost of 150.1409915422891 units per production decision. If the machine was not producing the same item in the previous period, a startup cost of 100.0821369467442 units is incurred. The exact quantity of each item to produce in each period must be determined, ensuring that the production quantity, plus a scaling factor of 10.00723193346443 units for startup, does not exceed the machine's capacity constraint of 80.13191751080457 units.

Inventory and backlog decisions must also be made. Holding inventory for Item 0 costs 1.001887559564105 units per period, for Item 1 costs 1.008465044664585 units, and for Item 2 costs 1.004424272477156 units. Backlogging Item 0 costs 8.001645451260206 units, Item 1 costs 8.019811444970745 units, and Item 2 costs 8.019590051695724 units per period.

The objective is to minimize the total cost, which includes production costs, startup costs, holding costs for storing inventory, and backlog costs for unmet demand. Constraints include demand fulfillment, where the sum of the previous period’s inventory (or backlog) and the current production must equal the demand for that period plus the current inventory (or backlog). The machine can produce only one item at a time, and production and startup decisions are binary (either yes or no). Additionally, production quantities, inventory levels, and backlogs must be non-negative.

For example, in Period 0, if Item 0 is produced, a production cost of 150.1409915422891 units and a startup cost of 100.0821369467442 units are incurred. The production quantity, plus 10.00723193346443 units for startup, must not exceed 80.13191751080457 units. The produced quantity, minus the demand of 20.18494518721846 units, will determine the inventory or backlog for Period 0. The task is to determine the optimal production schedule, inventory levels, and backlogs for all items across all periods to minimize the total cost while satisfying all constraints.
```

### 4. spec.json (`spec` and `warnings`)

```json
"production_cost": {"base":150.1409915422891,"perturb":{"mode":"rel","r":0.5}}
"startup_cost": {"base":100.0821369467442,"perturb":{"mode":"rel","r":0.5}}
"startup_scaling_factor": {"base":10.00723193346443,"perturb":{"mode":"rel","r":0.5}}
"machine_capacity": {"base":80.13191751080457,"perturb":{"mode":"rel","r":0.3}}
"holding_cost": {"base":[1.001887559564105,1.008465044664585,1.004424272477156],"perturb":{"mode":"rel","r":0.5}}
"backlog_cost": {"base":[8.001645451260206,8.019811444970745,8.019590051695724],"perturb":{"mode":"rel","r":0.5}}
"demand_period0": {"base":[20.18494518721846,20.18494518721846,20.18494518721846],"perturb":{"mode":"rel","r":0.3}}
```

Warnings:

```
none
```

### 5. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    production_cost = params["production_cost"]
    startup_cost = params["startup_cost"]
    startup_scaling_factor = params["startup_scaling_factor"]
    machine_capacity = params["machine_capacity"]
    holding_cost = params["holding_cost"]
    backlog_cost = params["backlog_cost"]
    demand_period0 = params["demand_period0"]

    items = [0, 1, 2]
    periods = [0, 1, 2, 3, 4]

    demand = {}
    for i in items:
        for t in periods:
            demand[i, t] = demand_period0[i]

    model = pyo.ConcreteModel()

    model.item_set = pyo.Set(initialize=items)
    model.period_set = pyo.Set(initialize=periods)

    model.produce = pyo.Var(model.item_set, model.period_set, domain=pyo.Binary)
    model.startup = pyo.Var(model.item_set, model.period_set, domain=pyo.Binary)

    model.prod_qty = pyo.Var(model.item_set, model.period_set, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.item_set, model.period_set, domain=pyo.NonNegativeReals)
    model.backlog = pyo.Var(model.item_set, model.period_set, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        total = 0
        for i in m.item_set:
            for t in m.period_set:
                total += production_cost * m.produce[i, t]
                total += startup_cost * m.startup[i, t]
                total += holding_cost[i] * m.inventory[i, t]
                total += backlog_cost[i] * m.backlog[i, t]
        return total

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def capacity_rule(m, t):
        return sum(m.prod_qty[i, t] for i in m.item_set) + \
               startup_scaling_factor * sum(m.startup[i, t] for i in m.item_set) <= machine_capacity

    model.capacity_con = pyo.Constraint(model.period_set, rule=capacity_rule)

    def one_item_rule(m, t):
        return sum(m.produce[i, t] for i in m.item_set) <= 1

    model.one_item_con = pyo.Constraint(model.period_set, rule=one_item_rule)

    def prod_link_rule(m, i, t):
        return m.prod_qty[i, t] <= machine_capacity * m.produce[i, t]

    model.prod_link_con = pyo.Constraint(model.item_set, model.period_set, rule=prod_link_rule)

    def startup_link_rule(m, i, t):
        if t == 0:
            return m.startup[i, t] >= m.produce[i, t]
        return m.startup[i, t] >= m.produce[i, t] - m.produce[i, t - 1]

    model.startup_link_con = pyo.Constraint(model.item_set, model.period_set, rule=startup_link_rule)

    def balance_rule(m, i, t):
        if t == 0:
            prev_inv = 0
            prev_backlog = 0
        else:
            prev_inv = m.inventory[i, t - 1]
            prev_backlog = m.backlog[i, t - 1]
        return prev_inv - prev_backlog + m.prod_qty[i, t] == demand[i, t] + m.inventory[i, t] - m.backlog[i, t]

    model.balance_con = pyo.Constraint(model.item_set, model.period_set, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"I":[0,1,2],"T":[0,1,2,3,4],"Tplus":[1,2,3,4]},"params":{"production_cost":"params['production_cost']","startup_cost":"params['startup_cost']","startup_scaling_factor":"params['startup_scaling_factor']","machine_capacity":"params['machine_capacity']","holding_cost":"params['holding_cost'][i]","backlog_cost":"params['backlog_cost'][i]","demand_period0":"params['demand_period0'][i]"},"assumptions":["Unspecified demand in periods 1-4 is zero.","Initial inventory, backlog, and production state are zero.","Terminal backlog is permitted."],"variables":{"produce[i,t]":"binary","startup[i,t]":"binary","quantity[i,t]":"nonnegative continuous","inventory[i,t]":"nonnegative continuous","backlog[i,t]":"nonnegative continuous"},"constraints":["For each t: sum_i produce[i,t] <= 1.","For each i,t: quantity[i,t] <= machine_capacity*produce[i,t].","For each t: sum_i (quantity[i,t]+startup_scaling_factor*startup[i,t]) <= machine_capacity.","For each i: startup[i,0] = produce[i,0].","For each i,t>0: startup[i,t] >= produce[i,t]-produce[i,t-1].","For each i,t>0: startup[i,t] <= produce[i,t].","For each i,t>0: startup[i,t] <= 1-produce[i,t-1].","For each i,t: previous_inventory-previous_backlog+quantity[i,t] = demand[i,t]+inventory[i,t]-backlog[i,t], with zero initial inventory/backlog and demand[i,t]=demand_period0[i] if t=0 else zero."],"objective":"Minimize sum_i,t (production_cost*produce[i,t]+startup_cost*startup[i,t]+holding_cost[i]*inventory[i,t]+backlog_cost[i]*backlog[i,t])."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 2)
    model.T = pyo.RangeSet(0, 4)
    model.Tplus = pyo.RangeSet(1, 4)

    model.production_cost = pyo.Param(initialize=params["production_cost"])
    model.startup_cost = pyo.Param(initialize=params["startup_cost"])
    model.startup_scaling_factor = pyo.Param(
        initialize=params["startup_scaling_factor"]
    )
    model.machine_capacity = pyo.Param(initialize=params["machine_capacity"])
    model.holding_cost = pyo.Param(
        model.I,
        initialize={i: params["holding_cost"][i] for i in model.I},
    )
    model.backlog_cost = pyo.Param(
        model.I,
        initialize={i: params["backlog_cost"][i] for i in model.I},
    )
    model.demand_period0 = pyo.Param(
        model.I,
        initialize={i: params["demand_period0"][i] for i in model.I},
    )

    model.produce = pyo.Var(model.I, model.T, domain=pyo.Binary)
    model.startup = pyo.Var(model.I, model.T, domain=pyo.Binary)
    model.quantity = pyo.Var(model.I, model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.I, model.T, domain=pyo.NonNegativeReals)
    model.backlog = pyo.Var(model.I, model.T, domain=pyo.NonNegativeReals)

    def single_item_rule(instance, t):
        return sum(instance.produce[i, t] for i in instance.I) <= 1

    model.single_item_limit = pyo.Constraint(model.T, rule=single_item_rule)

    def production_link_rule(instance, i, t):
        return (
            instance.quantity[i, t]
            <= instance.machine_capacity * instance.produce[i, t]
        )

    model.production_link = pyo.Constraint(
        model.I, model.T, rule=production_link_rule
    )

    def capacity_rule(instance, t):
        return (
            sum(
                instance.quantity[i, t]
                + instance.startup_scaling_factor * instance.startup[i, t]
                for i in instance.I
            )
            <= instance.machine_capacity
        )

    model.capacity_limit = pyo.Constraint(model.T, rule=capacity_rule)

    def initial_startup_rule(instance, i):
        return instance.startup[i, 0] == instance.produce[i, 0]

    model.initial_startup = pyo.Constraint(model.I, rule=initial_startup_rule)

    def startup_lower_rule(instance, i, t):
        return (
            instance.startup[i, t]
            >= instance.produce[i, t] - instance.produce[i, t - 1]
        )

    model.startup_lower = pyo.Constraint(
        model.I, model.Tplus, rule=startup_lower_rule
    )

    def startup_current_rule(instance, i, t):
        return instance.startup[i, t] <= instance.produce[i, t]

    model.startup_current_limit = pyo.Constraint(
        model.I, model.Tplus, rule=startup_current_rule
    )

    def startup_previous_rule(instance, i, t):
        return instance.startup[i, t] <= 1 - instance.produce[i, t - 1]

    model.startup_previous_limit = pyo.Constraint(
        model.I, model.Tplus, rule=startup_previous_rule
    )

    def balance_rule(instance, i, t):
        previous_net_inventory = (
            0
            if t == 0
            else instance.inventory[i, t - 1] - instance.backlog[i, t - 1]
        )
        demand = instance.demand_period0[i] if t == 0 else 0
        return (
            previous_net_inventory + instance.quantity[i, t]
            == demand + instance.inventory[i, t] - instance.backlog[i, t]
        )

    model.demand_balance = pyo.Constraint(model.I, model.T, rule=balance_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.production_cost * model.produce[i, t]
            + model.startup_cost * model.startup[i, t]
            + model.holding_cost[i] * model.inventory[i, t]
            + model.backlog_cost[i] * model.backlog[i, t]
            for i in model.I
            for t in model.T
        ),
        sense=pyo.minimize,
    )

    # HiGHS can raise RuntimeError when no feasible solution can be loaded.
    # Determine success solely by whether the objective can be evaluated.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    production_cost = params["production_cost"]
    startup_cost = params["startup_cost"]
    startup_scaling_factor = params["startup_scaling_factor"]
    machine_capacity = params["machine_capacity"]
    holding_cost = params["holding_cost"]      # list of 3
    backlog_cost = params["backlog_cost"]       # list of 3
    demand_period0 = params["demand_period0"]  # list of 3

    num_items = 3
    num_periods = 5
    items = range(num_items)
    periods = range(num_periods)

    # Demands: period 0 from params, periods 1-4 set to 0 (not given)
    demand = {}
    for i in items:
        demand[(i, 0)] = demand_period0[i]
        for t in range(1, num_periods):
            demand[(i, t)] = 0.0

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    # Binary: produce item i in period t
    x = model.addVars(num_items, num_periods, vtype=GRB.BINARY, name="x")
    # Binary: startup for item i in period t
    s = model.addVars(num_items, num_periods, vtype=GRB.BINARY, name="s")
    # Continuous: production quantity for item i in period t
    q = model.addVars(num_items, num_periods, lb=0.0, name="q")
    # Continuous: inventory for item i at end of period t
    inv = model.addVars(num_items, num_periods, lb=0.0, name="inv")
    # Continuous: backlog for item i at end of period t
    bl = model.addVars(num_items, num_periods, lb=0.0, name="bl")

    # Objective
    obj = gp.quicksum(
        production_cost * x[i, t]
        + startup_cost * s[i, t]
        + holding_cost[i] * inv[i, t]
        + backlog_cost[i] * bl[i, t]
        for i in items for t in periods
    )
    model.setObjective(obj, GRB.MINIMIZE)

    # Demand balance constraints
    for i in items:
        for t in periods:
            if t == 0:
                # No prior inventory or backlog
                model.addConstr(
                    q[i, t] - demand[(i, t)] == inv[i, t] - bl[i, t],
                    name=f"balance_{i}_{t}"
                )
            else:
                model.addConstr(
                    inv[i, t-1] - bl[i, t-1] + q[i, t] - demand[(i, t)] == inv[i, t] - bl[i, t],
                    name=f"balance_{i}_{t}"
                )

    # Only one item produced per period
    for t in periods:
        model.addConstr(
            gp.quicksum(x[i, t] for i in items) <= 1,
            name=f"one_item_{t}"
        )

    # Production quantity only if item is selected
    for i in items:
        for t in periods:
            model.addConstr(q[i, t] <= machine_capacity * x[i, t], name=f"prod_if_selected_{i}_{t}")

    # Capacity constraint: production + startup_scaling * startup <= machine_capacity
    for t in periods:
        model.addConstr(
            gp.quicksum(q[i, t] + startup_scaling_factor * s[i, t] for i in items) <= machine_capacity,
            name=f"capacity_{t}"
        )

    # Startup logic: s[i,t] = 1 if x[i,t]=1 and x[i,t-1]=0
    for i in items:
        for t in periods:
            if t == 0:
                # At period 0, there's no previous period; startup occurs if produced
                model.addConstr(s[i, t] == x[i, t], name=f"startup_period0_{i}")
            else:
                # s[i,t] >= x[i,t] - x[i,t-1]
                model.addConstr(s[i, t] >= x[i, t] - x[i, t-1], name=f"startup_lb_{i}_{t}")
                # s[i,t] <= x[i,t]
                model.addConstr(s[i, t] <= x[i, t], name=f"startup_ub1_{i}_{t}")
                # s[i,t] <= 1 - x[i,t-1]
                model.addConstr(s[i, t] <= 1 - x[i, t-1], name=f"startup_ub2_{i}_{t}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 6. Objective values

Rules that certify it: gate, panel_base_2of3, ind_gate.

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 2360.897154905569 (optimal) | 1235.5699207670264 (optimal) | 1235.5699207670268 (optimal) |
| 1 | 1538.5460334950262 (optimal) | 833.0227579815216 (optimal) | 833.0227579815216 (optimal) |
| 2 | 2481.1465856341642 (optimal) | 1072.6909967855872 (optimal) | 1072.6909967855872 (optimal) |
| 3 | 2178.036698600349 (optimal) | 958.0662781369768 (optimal) | 958.0662781369768 (optimal) |
| 4 | 1998.364851904666 (optimal) | 1126.735204315586 (optimal) | 1126.7352043155815 (optimal) |
| 5 | 2576.6965526759623 (optimal) | 1293.1074429258238 (optimal) | 1293.1074429258235 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 2360.897154905569 (optimal) | 1235.5699207670264 (optimal) | 1235.5699207670268 (optimal) |
| 1 | 1538.5460334950262 (optimal) | 833.0227579815216 (optimal) | 833.0227579815216 (optimal) |
| 2 | 2481.1465856341642 (optimal) | 1072.6909967855872 (optimal) | 1072.6909967855872 (optimal) |
| 3 | 2178.036698600349 (optimal) | 958.0662781369768 (optimal) | 958.0662781369768 (optimal) |
| 4 | 1998.364851904666 (optimal) | 1126.735204315586 (optimal) | 1126.7352043155815 (optimal) |
| 5 | 2576.6965526759623 (optimal) | 1293.1074429258238 (optimal) | 1293.1074429258235 (optimal) |


## 12. conf_66014 (confirm (OptMATH-200))

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `conf_66014` |
| Set | confirm (OptMATH-200) |
| Source record | OptMATH-Train record 66014 |
| Optimization sense | not determined from the problem text (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 11250495.529411767 |
| Label | 11417460.619134724 |
| Rules that certify it | gate, panel_base_2of3, ind_gate (values: 11250495.529411767) |
| Label source | `artifacts/v2/optmath_200/problems.csv`, OptMATH-Train record 66014, field `answer`; the dataset stores no solution |

### 2. Certifying clique of panel_base_2of3 and values at instance 0

Families that agree at the stated instance (abs(a-b) <= 1e-4*max(1,|a|,|b|)): B (GPT-6.1 Sol) and C (Claude Sonnet 5.5). The third family: A (DeepSeek-V4-Flash) returns none.

| Family | Program | Value at instance 0 | Status at instance 0 | In the certifying clique | Matches the label (round_aware) |
|---|---|---|---|---|---|
| A (DeepSeek-V4-Flash) | A-direct.py | none | crash:raise ValueError( \| ValueError: Attempting to declare a block component using the name of a reserved attribute: \| items | no | no |
| B (GPT-6.1 Sol) | B-structured.py | 11250495.529411767 | optimal | yes | no |
| C (Claude Sonnet 5.5) | C-direct.py | 11250495.529411767 | optimal | yes | no |

### 3. Problem text

```
Production Planning for a Manufacturing Facility

You are tasked with managing the production planning for a manufacturing facility that produces 49 different types of items. Each item has a specific profit margin associated with it, and the facility aims to maximize its total profit while adhering to resource constraints and production limits.

#### Key Details:
1. **Profit Margins**: Each item generates a specific profit per unit produced. The profit margins for the items range from $300 to $399 per unit. For example:
   - Item 0 yields $346 per unit.
   - Item 1 yields $397 per unit.
   - Item 2 yields $387 per unit.
   - This pattern continues for all 49 items, with each item having its own unique profit margin.

2. **Resource Constraint**: The facility has a limited resource capacity of 433 units. Each item consumes a specific fraction of this resource per unit produced. For instance:
   - Producing one unit of Item 0 consumes approximately 0.0132 units of the resource.
   - Producing one unit of Item 1 consumes approximately 0.0149 units of the resource.
   - These consumption rates vary across all items, with some items consuming more or less of the resource.

3. **Production Limits**: Each item has a maximum production limit, which represents the highest number of units that can be produced for that item. These limits vary significantly:
   - Item 0 can be produced up to 733 units.
   - Item 1 can be produced up to 759 units.
   - Item 2 can be produced up to 717 units.
   - These upper bounds are specific to each item and must not be exceeded.

#### Objective:
Your goal is to determine the optimal number of units to produce for each item to maximize the total profit, while ensuring that the total resource consumption does not exceed the available 433 units. Additionally, the production quantities must respect the upper and lower bounds for each item (i.e., production cannot be negative and cannot exceed the specified maximum limits).

#### Constraints:
- **Resource Usage**: The total resource consumption across all items must not exceed 433 units. For example, if you produce 100 units of Item 0, it will consume approximately 1.32 units of the resource (100 × 0.0132). This calculation must be done for all items, and the sum must stay within the resource limit.
- **Production Bounds**: Each item has a minimum production quantity of 0 units and a maximum production quantity as specified (e.g., 733 units for Item 0, 759 units for Item 1, etc.).

#### Example:
Suppose you decide to produce 500 units of Item 0, 400 units of Item 1, and 300 units of Item 2. The resource consumption would be:
- Item 0: 500 × 0.0132 = 6.6 units.
- Item 1: 400 × 0.0149 = 5.96 units.
- Item 2: 300 × 0.0135 = 4.05 units.
- Total resource consumption: 6.6 + 5.96 + 4.05 = 16.61 units.

This is well within the 433-unit resource limit, but you must ensure that the production quantities for all 49 items collectively do not exceed this limit while maximizing the total profit.

#### Final Goal:
Determine the optimal production quantities for all 49 items to maximize the total profit, ensuring that the resource constraint is satisfied and that production quantities remain within their specified bounds.
```

### 4. spec.json (`spec` and `warnings`)

```json
"profit_margins": {"base":[346,397,387,300,399,350,320,310,390,360,370,330,340,380,395,305,315,325,335,345,355,365,375,385,398,302,312,322,332,342,352,362,372,382,392,303,313,323,333,343,353,363,373,383,393,304,314,324,334],"perturb":{"mode":"rel","r":0.25}}
"resource_capacities": {"base":[0.0132,0.0149,0.0135,0.0148,0.0131,0.0147,0.0134,0.0146,0.0133,0.0145,0.0136,0.0144,0.0137,0.0143,0.0138,0.0142,0.0139,0.0141,0.014,0.013,0.0129,0.015,0.0128,0.0151,0.0127,0.0152,0.0126,0.0153,0.0125,0.0154,0.0124,0.0155,0.0123,0.0156,0.0122,0.0157,0.0121,0.0158,0.012,0.0159,0.0119,0.016,0.0118,0.0161,0.0117,0.0162,0.0116,0.0163,0.0115],"perturb":{"mode":"rel","r":0.3}}
"resource_budget": {"base":433,"perturb":{"mode":"rel","r":0.25}}
"production_limits": {"base":[733,759,717,700,780,720,740,750,710,760,730,750,740,780,700,720,740,760,780,700,720,740,760,780,700,720,740,760,780,700,720,740,760,780,700,720,740,760,780,700,720,740,760,780,700,720,740,760,780],"perturb":{"mode":"rel","r":0.2}}
```

Warnings:

```
none
```

### 5. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_margins = params["profit_margins"]
    resource_capacities = params["resource_capacities"]
    resource_budget = params["resource_budget"]
    production_limits = params["production_limits"]

    n = len(profit_margins)

    model = pyo.ConcreteModel()
    model.items = pyo.RangeSet(0, n - 1)

    model.produce = pyo.Var(model.items, within=pyo.NonNegativeReals)

    def profit_rule(mdl):
        return sum(profit_margins[i] * mdl.produce[i] for i in mdl.items)

    model.total_profit = pyo.Objective(rule=profit_rule, sense=pyo.maximize)

    def resource_rule(mdl):
        return sum(resource_capacities[i] * mdl.produce[i] for i in mdl.items) <= resource_budget

    model.resource_con = pyo.Constraint(rule=resource_rule)

    def upper_rule(mdl, i):
        return mdl.produce[i] <= production_limits[i]

    model.upper_con = pyo.Constraint(model.items, rule=upper_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"I":"0..48"},"params":{"profit_margins":"real[I]","resource_capacities":"real[I]","resource_budget":"real","production_limits":"real[I]"},"variables":{"production":"nonnegative continuous[I]"},"constraints":["sum(resource_capacities[i]*production[i] for i in I) <= resource_budget","production[i] <= production_limits[i] for i in I"],"objective":"maximize sum(profit_margins[i]*production[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.item_set = pyo.RangeSet(0, 48)

    model.profit_margins = pyo.Param(
        model.item_set,
        initialize={i: params["profit_margins"][i] for i in model.item_set},
        within=pyo.Reals,
    )
    model.resource_capacities = pyo.Param(
        model.item_set,
        initialize={i: params["resource_capacities"][i] for i in model.item_set},
        within=pyo.Reals,
    )
    model.resource_budget = pyo.Param(
        initialize=params["resource_budget"],
        within=pyo.Reals,
    )
    model.production_limits = pyo.Param(
        model.item_set,
        initialize={i: params["production_limits"][i] for i in model.item_set},
        within=pyo.Reals,
    )

    model.production = pyo.Var(model.item_set, domain=pyo.NonNegativeReals)

    model.resource_constraint = pyo.Constraint(
        expr=sum(
            model.resource_capacities[i] * model.production[i]
            for i in model.item_set
        ) <= model.resource_budget
    )

    def production_limit_rule(instance, i):
        return instance.production[i] <= instance.production_limits[i]

    model.production_limit_constraints = pyo.Constraint(
        model.item_set,
        rule=production_limit_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_margins[i] * model.production[i]
            for i in model.item_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_margins = params["profit_margins"]
    resource_capacities = params["resource_capacities"]
    resource_budget = params["resource_budget"]
    production_limits = params["production_limits"]

    n_items = len(profit_margins)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_items, lb=0.0, name="x")
    for i in range(n_items):
        x[i].ub = production_limits[i]

    model.setObjective(
        gp.quicksum(profit_margins[i] * x[i] for i in range(n_items)),
        GRB.MAXIMIZE
    )

    model.addConstr(
        gp.quicksum(resource_capacities[i] * x[i] for i in range(n_items)) <= resource_budget,
        name="resource"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 6. Objective values

Rules that certify it: gate, panel_base_2of3, ind_gate.

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:raise ValueError( \| ValueError: Attempting to declare a block component using the name of a reserved attribute: \| items) | 11250495.529411767 (optimal) | 11250495.529411767 (optimal) |
| 1 | none (crash:raise ValueError( \| ValueError: Attempting to declare a block component using the name of a reserved attribute: \| items) | 12482853.96761495 (optimal) | 12482853.967614947 (optimal) |
| 2 | none (crash:raise ValueError( \| ValueError: Attempting to declare a block component using the name of a reserved attribute: \| items) | 10025133.09975621 (optimal) | 10025133.09975621 (optimal) |
| 3 | none (crash:raise ValueError( \| ValueError: Attempting to declare a block component using the name of a reserved attribute: \| items) | 9692990.77301773 (optimal) | 9692990.773017729 (optimal) |
| 4 | none (crash:raise ValueError( \| ValueError: Attempting to declare a block component using the name of a reserved attribute: \| items) | 10149592.228786899 (optimal) | 10149592.228786899 (optimal) |
| 5 | none (crash:raise ValueError( \| ValueError: Attempting to declare a block component using the name of a reserved attribute: \| items) | 12099942.290959395 (optimal) | 12099942.2909594 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:raise ValueError( \| ValueError: Attempting to declare a block component using the name of a reserved attribute: \| items) | 11250495.529411767 (optimal) | 11250495.529411767 (optimal) |
| 1 | none (crash:raise ValueError( \| ValueError: Attempting to declare a block component using the name of a reserved attribute: \| items) | 12482853.96761495 (optimal) | 12482853.967614947 (optimal) |
| 2 | none (crash:raise ValueError( \| ValueError: Attempting to declare a block component using the name of a reserved attribute: \| items) | 10025133.09975621 (optimal) | 10025133.09975621 (optimal) |
| 3 | none (crash:raise ValueError( \| ValueError: Attempting to declare a block component using the name of a reserved attribute: \| items) | 9692990.77301773 (optimal) | 9692990.773017729 (optimal) |
| 4 | none (crash:raise ValueError( \| ValueError: Attempting to declare a block component using the name of a reserved attribute: \| items) | 10149592.228786899 (optimal) | 10149592.228786899 (optimal) |
| 5 | none (crash:raise ValueError( \| ValueError: Attempting to declare a block component using the name of a reserved attribute: \| items) | 12099942.290959395 (optimal) | 12099942.2909594 (optimal) |


## 13. conf_120613 (confirm (OptMATH-200))

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `conf_120613` |
| Set | confirm (OptMATH-200) |
| Source record | OptMATH-Train record 120613 |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 1844.0 |
| Label | 1819.0 |
| Rules that certify it | gate, panel_base_2of3, ind_gate (values: 1844.0) |
| Label source | `artifacts/v2/optmath_200/problems.csv`, OptMATH-Train record 120613, field `answer`; the dataset stores no solution |

### 2. Certifying clique of panel_base_2of3 and values at instance 0

Families that agree at the stated instance (abs(a-b) <= 1e-4*max(1,|a|,|b|)): A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5). The third family: B (GPT-6.1 Sol) returns 1839.0.

| Family | Program | Value at instance 0 | Status at instance 0 | In the certifying clique | Matches the label (round_aware) |
|---|---|---|---|---|---|
| A (DeepSeek-V4-Flash) | A-direct.py | 1844.0 | optimal | yes | no |
| B (GPT-6.1 Sol) | B-structured.py | 1839.0 | optimal | no | no |
| C (Claude Sonnet 5.5) | C-direct.py | 1844.0 | optimal | yes | no |

### 3. Problem text

```
The problem involves optimizing the flow of goods across a logistics network to minimize total costs, which include transportation costs and facility installation costs. The network consists of multiple interconnected locations, and there are two commodities to be transported: Commodity 1 originates at Location 0 and must be delivered to Location 3, and Commodity 2 originates at Location 1 and must be delivered to Location 2. The transportation costs vary by route and commodity: transporting Commodity 1 from Location 0 to Location 3 costs 8 units per unit of flow, while transporting Commodity 2 from Location 1 to Location 2 costs 22 units per unit of flow. Other transportation costs include 16 units for Commodity 1 from Location 0 to Location 1, 24 units for Commodity 1 from Location 0 to Location 2, and 11 units for Commodity 2 from Location 1 to Location 3.

Facilities can be installed on specific routes to handle the flow of goods. Each facility has an installation cost and provides a specific capacity. For example, installing a facility on the route from Location 0 to Location 3 costs 961 units and provides a capacity of 607 units. Similarly, installing a facility on the route from Location 1 to Location 2 costs 853 units and provides a capacity of 594 units. Other facility installation costs include 948 units for Location 1 to Location 3, 927 units for Location 2 to Location 0, 833 units for Location 2 to Location 1, 913 units for Location 3 to Location 1, and 976 units for Location 3 to Location 2. The capacities for these facilities are 610, 552, 603, 578, and 558 units, respectively.

The flow of goods must satisfy several constraints. First, flow conservation must be maintained: the total flow of each commodity into a location must equal the total flow out of that location, adjusted for whether the location is the origin or destination of the commodity. For example, at Location 0, the flow of Commodity 1 into Location 3 must equal the flow out of Location 2. At Location 1, the flow of Commodity 2 into Location 2 must exceed the flow out of Location 3 by 1 unit. Second, capacity constraints must be respected: the total flow of all commodities on a route cannot exceed the capacity provided by the installed facilities. For example, the combined flow of Commodity 1 and Commodity 2 on the route from Location 0 to Location 3 must not exceed 607 units multiplied by the number of facilities installed on that route. Third, the flow of each commodity on any route must be between 0 and 1, representing the fraction of the commodity transported on that route.

The number of facilities installed on each route must be a non-negative integer. For example, you can install 0, 1, 2, or more facilities on the route from Location 0 to Location 3, but you cannot install a fraction of a facility.

The objective is to minimize the total cost, which includes the cost of transporting all commodities across the network and the cost of installing and maintaining facilities on the routes. For example, the total transportation cost for Commodity 1 from Location 0 to Location 3 is 8 units per unit of flow, and the total installation cost for facilities on the route from Location 1 to Location 2 is 853 units per facility. Other transportation costs include 16 units for Commodity 1 from Location 0 to Location 1, 24 units for Commodity 1 from Location 0 to Location 2, and 11 units for Commodity 2 from Location 1 to Location 3. The total cost also includes facility installation costs of 961, 853, 948, 927, 833, 913, and 976 units for the respective routes. By carefully balancing the flow of goods and the installation of facilities, the goal is to achieve the lowest possible total cost while ensuring all commodities reach their destinations and all capacity constraints are satisfied.
```

### 4. spec.json (`spec` and `warnings`)

```json
"transport_cost_c1_0_3": {"base":8,"perturb":{"mode":"rel","r":0.5}}
"transport_cost_c2_1_2": {"base":22,"perturb":{"mode":"rel","r":0.5}}
"transport_cost_c1_0_1": {"base":16,"perturb":{"mode":"rel","r":0.5}}
"transport_cost_c1_0_2": {"base":24,"perturb":{"mode":"rel","r":0.5}}
"transport_cost_c2_1_3": {"base":11,"perturb":{"mode":"rel","r":0.5}}
"install_cost_0_3": {"base":961,"perturb":{"mode":"rel","r":0.5}}
"capacity_0_3": {"base":607,"perturb":{"mode":"rel","r":0.5}}
"install_cost_1_2": {"base":853,"perturb":{"mode":"rel","r":0.5}}
"capacity_1_2": {"base":594,"perturb":{"mode":"rel","r":0.5}}
"install_cost_1_3": {"base":948,"perturb":{"mode":"rel","r":0.5}}
"capacity_1_3": {"base":610,"perturb":{"mode":"rel","r":0.5}}
"install_cost_2_0": {"base":927,"perturb":{"mode":"rel","r":0.5}}
"capacity_2_0": {"base":552,"perturb":{"mode":"rel","r":0.5}}
"install_cost_2_1": {"base":833,"perturb":{"mode":"rel","r":0.5}}
"capacity_2_1": {"base":603,"perturb":{"mode":"rel","r":0.5}}
"install_cost_3_1": {"base":913,"perturb":{"mode":"rel","r":0.5}}
"capacity_3_1": {"base":578,"perturb":{"mode":"rel","r":0.5}}
"install_cost_3_2": {"base":976,"perturb":{"mode":"rel","r":0.5}}
"capacity_3_2": {"base":558,"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

### 5. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Sets
    model.COMMODITIES = pyo.Set(initialize=[1, 2])
    model.LOCATIONS = pyo.Set(initialize=[0, 1, 2, 3])

    # Routes that have facility installation parameters
    facility_routes = [(0, 3), (1, 2), (1, 3), (2, 0), (2, 1), (3, 1), (3, 2)]
    model.FACILITY_ROUTES = pyo.Set(initialize=facility_routes, dimen=2)

    # Commodity-specific routes
    # Commodity 1: 0->3, 0->1, 0->2
    # Commodity 2: 1->2, 1->3
    c1_routes = [(0, 3), (0, 1), (0, 2)]
    c2_routes = [(1, 2), (1, 3)]

    # Transportation costs dictionary
    transport_cost = {}
    # Commodity 1
    transport_cost[(1, 0, 3)] = params["transport_cost_c1_0_3"]
    transport_cost[(1, 0, 1)] = params["transport_cost_c1_0_1"]
    transport_cost[(1, 0, 2)] = params["transport_cost_c1_0_2"]
    # Commodity 2
    transport_cost[(2, 1, 2)] = params["transport_cost_c2_1_2"]
    transport_cost[(2, 1, 3)] = params["transport_cost_c2_1_3"]

    # Installation costs and capacities dictionary
    install_cost = {}
    capacity = {}
    install_cost[(0, 3)] = params["install_cost_0_3"]
    capacity[(0, 3)] = params["capacity_0_3"]
    install_cost[(1, 2)] = params["install_cost_1_2"]
    capacity[(1, 2)] = params["capacity_1_2"]
    install_cost[(1, 3)] = params["install_cost_1_3"]
    capacity[(1, 3)] = params["capacity_1_3"]
    install_cost[(2, 0)] = params["install_cost_2_0"]
    capacity[(2, 0)] = params["capacity_2_0"]
    install_cost[(2, 1)] = params["install_cost_2_1"]
    capacity[(2, 1)] = params["capacity_2_1"]
    install_cost[(3, 1)] = params["install_cost_3_1"]
    capacity[(3, 1)] = params["capacity_3_1"]
    install_cost[(3, 2)] = params["install_cost_3_2"]
    capacity[(3, 2)] = params["capacity_3_2"]

    # Decision Variables
    # Flow variables for each commodity on its routes, bounded 0 to 1
    def flow_c1_bounds(model, i, j):
        return (0, 1)
    def flow_c2_bounds(model, i, j):
        return (0, 1)

    model.FLOW_C1_ROUTES = pyo.Set(initialize=c1_routes, dimen=2)
    model.FLOW_C2_ROUTES = pyo.Set(initialize=c2_routes, dimen=2)

    model.flow_c1 = pyo.Var(model.FLOW_C1_ROUTES, domain=pyo.NonNegativeReals, bounds=(0, 1))
    model.flow_c2 = pyo.Var(model.FLOW_C2_ROUTES, domain=pyo.NonNegativeReals, bounds=(0, 1))

    # Integer facilities installed on each facility route
    model.facilities = pyo.Var(model.FACILITY_ROUTES, domain=pyo.NonNegativeIntegers)


    def flow_c1_dict_rule(model, i, j):
        return model.flow_c1[i, j]
    # We use the variable objects directly.

    # Objective:
    # Transportation cost for commodity 1 on its routes
    # Transportation cost for commodity 2 on its routes
    # Installation cost for facilities on all facility routes
    def obj_rule(model):
        trans_c1 = sum(
            transport_cost[(1, i, j)] * model.flow_c1[i, j] for (i, j) in c1_routes
        )
        trans_c2 = sum(
            transport_cost[(2, i, j)] * model.flow_c2[i, j] for (i, j) in c2_routes
        )
        install = sum(
            install_cost[(i, j)] * model.facilities[i, j] for (i, j) in facility_routes
        )
        return trans_c1 + trans_c2 + install

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Capacity constraints:
    # On the shared route 0->3: flow_c1[0,3] + 0 (no commodity 2 on 0->3) <= capacity_0_3 * facilities[0,3]
    # Actually, the problem says "combined flow of Commodity 1 and Commodity 2 on the route from Location 0 to Location 3 must not exceed 607 * facilities".
    # Commodity 2 does not use route 0->3, so only flow_c1[0,3] contributes.
    def cap_0_3_rule(model):
        return model.flow_c1[0, 3] <= capacity[(0, 3)] * model.facilities[0, 3]
    model.cap_0_3 = pyo.Constraint(rule=cap_0_3_rule)

    # On route 1->2: commodity 2 flows. Also maybe commodity 1? Commodity 1 has routes 0->3, 0->1, 0->2, not 1->2. So only commodity 2.
    def cap_1_2_rule(model):
        return model.flow_c2[1, 2] <= capacity[(1, 2)] * model.facilities[1, 2]
    model.cap_1_2 = pyo.Constraint(rule=cap_1_2_rule)

    # On route 1->3: commodity 2 flows.
    def cap_1_3_rule(model):
        return model.flow_c2[1, 3] <= capacity[(1, 3)] * model.facilities[1, 3]
    model.cap_1_3 = pyo.Constraint(rule=cap_1_3_rule)

    # On route 2->0: no commodity flows defined (commodity 1 does not use it, commodity 2 does not use it).
    # But facility may be installed. Since no flow, the capacity constraint is 0 <= capacity * facilities, which is always true.
    # We omit it since no flow uses it.

    # On route 2->1: no commodity flows defined.
    # Omit.

    # On route 3->1: no commodity flows defined.
    # Omit.

    # On route 3->2: no commodity flows defined.
    # Omit.

    # Flow conservation constraints:

    # Commodity 1: originates at location 0, destination at location 3.
    # At location 0: total flow out - total flow in = 1 (supply)
    # At location 3: total flow in - total flow out = 1 (demand)
    # At other locations: flow in = flow out.

    # Commodity 1 routes: (0,3), (0,1), (0,2)
    # At location 0: outflow = flow_c1[0,3] + flow_c1[0,1] + flow_c1[0,2], inflow = 0 (no incoming routes for commodity 1)
    # So outflow - inflow = 1 -> flow_c1[0,3] + flow_c1[0,1] + flow_c1[0,2] = 1

    def c1_balance_0_rule(model):
        return model.flow_c1[0, 3] + model.flow_c1[0, 1] + model.flow_c1[0, 2] == 1
    model.c1_balance_0 = pyo.Constraint(rule=c1_balance_0_rule)

    # At location 3: inflow = flow_c1[0,3], outflow = 0 (no outgoing routes for commodity 1)
    # inflow - outflow = 1 -> flow_c1[0,3] = 1

    def c1_balance_3_rule(model):
        return model.flow_c1[0, 3] == 1
    model.c1_balance_3 = pyo.Constraint(rule=c1_balance_3_rule)

    # At location 1: inflow = flow_c1[0,1], outflow = 0 (no outgoing routes for commodity 1)
    # Since location 1 is not origin or destination for commodity 1, inflow = outflow -> flow_c1[0,1] = 0

    def c1_balance_1_rule(model):
        return model.flow_c1[0, 1] == 0
    model.c1_balance_1 = pyo.Constraint(rule=c1_balance_1_rule)

    # At location 2: inflow = flow_c1[0,2], outflow = 0
    # Since location 2 is not origin or destination for commodity 1, inflow = outflow -> flow_c1[0,2] = 0

    def c1_balance_2_rule(model):
        return model.flow_c1[0, 2] == 0
    model.c1_balance_2 = pyo.Constraint(rule=c1_balance_2_rule)

    # Commodity 2: originates at location 1, destination at location 2.
    # Routes: (1,2), (1,3)

    # At location 1: outflow = flow_c2[1,2] + flow_c2[1,3], inflow = 0 (no incoming routes for commodity 2)
    # But the problem says "At Location 1, the flow of Commodity 2 into Location 2 must exceed the flow out of Location 3 by 1 unit."
    # This is a bit ambiguous. "flow of Commodity 2 into Location 2" refers to flow_c2[1,2] (route 1->2).
    # "flow out of Location 3" likely refers to flow_c2[1,3] (route 1->3)?? No, flow out of Location 3 would be a route from 3 to somewhere.
    # But commodity 2 has no route from 3. The only route involving 3 for commodity 2 is 1->3 (into location 3).
    # So "flow out of Location 3" might be a misinterpretation. Perhaps it means flow_c2[1,3]?? No.
    # Let's re-read: "At Location 1, the flow of Commodity 2 into Location 2 must exceed the flow out of Location 3 by 1 unit."
    # This is confusing. Possibly it means: inflow at location 1 (from origin) equals outflow? Or it's a supply constraint?
    # Actually, the origin is location 1. The supply is 1 unit. So outflow - inflow = 1.
    # Outflow = flow_c2[1,2] + flow_c2[1,3]. Inflow = 0. So flow_c2[1,2] + flow_c2[1,3] = 1.
    # The statement "flow of Commodity 2 into Location 2 must exceed the flow out of Location 3 by 1 unit" might be a garbled version of the conservation constraint.
    # Let's interpret: At location 1, supply = 1: flow_c2[1,2] + flow_c2[1,3] = 1.
    # At location 2: demand = 1: inflow = flow_c2[1,2] = 1.
    # At location 3: no demand, so inflow = flow_c2[1,3] = 0 (since not destination).
    # But that would force flow_c2[1,2] = 1 and flow_c2[1,3] = 0.
    # Let's check the statement: "the flow of Commodity 2 into Location 2 must exceed the flow out of Location 3 by 1 unit."
    # If "flow out of Location 3" refers to flow_c2[1,3] (which is into Location 3, not out), then flow_c2[1,2] - flow_c2[1,3] = 1.
    # Combined with flow_c2[1,2] + flow_c2[1,3] = 1, we get flow_c2[1,2] = 1, flow_c2[1,3] = 0.
    # That is consistent with the conservation constraints if location 3 is not a destination.
    # However, the statement says "flow out of Location 3", which is odd.
    # Let's just implement flow conservation with supply/demand:
    # At location 1 (origin): outflow - inflow = 1 -> flow_c2[1,2] + flow_c2[1,3] = 1
    # At location 2 (destination): inflow - outflow = 1 -> flow_c2[1,2] = 1
    # At location 3 (neither): inflow = outflow -> flow_c2[1,3] = 0 (since no outflow from 3)
    # This yields flow_c2[1,2] = 1, flow_c2[1,3] = 0.
    # Let's double-check: "the flow of Commodity 2 into Location 2 must exceed the flow out of Location 3 by 1 unit."
    # If flow_c2[1,2] - flow_c2[1,3] = 1, and flow_c2[1,2] + flow_c2[1,3] = 1, then indeed flow_c2[1,2] = 1, flow_c2[1,3] = 0.
    # So we'll use the conservation constraints as above, which are equivalent.

    def c2_balance_1_rule(model):
        return model.flow_c2[1, 2] + model.flow_c2[1, 3] == 1
    model.c2_balance_1 = pyo.Constraint(rule=c2_balance_1_rule)

    def c2_balance_2_rule(model):
        return model.flow_c2[1, 2] == 1
    model.c2_balance_2 = pyo.Constraint(rule=c2_balance_2_rule)

    def c2_balance_3_rule(model):
        return model.flow_c2[1, 3] == 0
    model.c2_balance_3 = pyo.Constraint(rule=c2_balance_3_rule)

    # Also need balance at location 0 for commodity 2? No routes for commodity 2 at location 0.
    # Not needed.

    # Solve
    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as e:
        return {"objective": None, "status": str(e)[:50]}
```

#### B-structured.py

```python
# IR (JSON):
# {
#   "sets": {
#     "nodes": [0, 1, 2, 3],
#     "commodities": [1, 2],
#     "arcs": [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 0], [2, 1], [3, 1], [3, 2]],
#     "facility_arcs": [[0, 3], [1, 2], [1, 3], [2, 0], [2, 1], [3, 1], [3, 2]]
#   },
#   "params": {
#     "transport_cost": {
#       "1,0,3": "transport_cost_c1_0_3",
#       "2,1,2": "transport_cost_c2_1_2",
#       "1,0,1": "transport_cost_c1_0_1",
#       "1,0,2": "transport_cost_c1_0_2",
#       "2,1,3": "transport_cost_c2_1_3"
#     },
#     "install_cost": {
#       "0,3": "install_cost_0_3",
#       "1,2": "install_cost_1_2",
#       "1,3": "install_cost_1_3",
#       "2,0": "install_cost_2_0",
#       "2,1": "install_cost_2_1",
#       "3,1": "install_cost_3_1",
#       "3,2": "install_cost_3_2"
#     },
#     "capacity": {
#       "0,3": "capacity_0_3",
#       "1,2": "capacity_1_2",
#       "1,3": "capacity_1_3",
#       "2,0": "capacity_2_0",
#       "2,1": "capacity_2_1",
#       "3,1": "capacity_3_1",
#       "3,2": "capacity_3_2"
#     }
#   },
#   "structural_data": {
#     "origins": {"1": 0, "2": 1},
#     "destinations": {"1": 3, "2": 2},
#     "demand_per_commodity": 1
#   },
#   "interpretation": [
#     "Only listed routes exist; every commodity can use every listed route.",
#     "Unspecified transportation costs are zero.",
#     "Capacity constraints apply only to facility_arcs; arcs 0->1 and 0->2 have no installation requirement.",
#     "Flow conservation follows the stated origins and destinations."
#   ],
#   "variables": {
#     "flow[k,i,j]": "continuous, 0 <= flow <= 1",
#     "facilities[i,j]": "nonnegative integer, indexed by facility_arcs"
#   },
#   "constraints": [
#     "For each commodity k and node v: sum_j flow[k,v,j] - sum_i flow[k,i,v] = 1 if v is origin[k], -1 if v is destination[k], otherwise 0.",
#     "For each facility arc (i,j): sum_k flow[k,i,j] <= capacity[i,j] * facilities[i,j]."
#   ],
#   "objective": "Minimize sum_(k,i,j with specified cost) transport_cost[k,i,j]*flow[k,i,j] + sum_(i,j in facility_arcs) install_cost[i,j]*facilities[i,j]."
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = (0, 1, 2, 3)
    commodities = (1, 2)
    arcs = (
        (0, 1),
        (0, 2),
        (0, 3),
        (1, 2),
        (1, 3),
        (2, 0),
        (2, 1),
        (3, 1),
        (3, 2),
    )
    facility_arcs = (
        (0, 3),
        (1, 2),
        (1, 3),
        (2, 0),
        (2, 1),
        (3, 1),
        (3, 2),
    )
    origins = {1: 0, 2: 1}
    destinations = {1: 3, 2: 2}

    transport_costs = {
        (1, 0, 3): params["transport_cost_c1_0_3"],
        (2, 1, 2): params["transport_cost_c2_1_2"],
        (1, 0, 1): params["transport_cost_c1_0_1"],
        (1, 0, 2): params["transport_cost_c1_0_2"],
        (2, 1, 3): params["transport_cost_c2_1_3"],
    }
    installation_costs = {
        (0, 3): params["install_cost_0_3"],
        (1, 2): params["install_cost_1_2"],
        (1, 3): params["install_cost_1_3"],
        (2, 0): params["install_cost_2_0"],
        (2, 1): params["install_cost_2_1"],
        (3, 1): params["install_cost_3_1"],
        (3, 2): params["install_cost_3_2"],
    }
    capacities = {
        (0, 3): params["capacity_0_3"],
        (1, 2): params["capacity_1_2"],
        (1, 3): params["capacity_1_3"],
        (2, 0): params["capacity_2_0"],
        (2, 1): params["capacity_2_1"],
        (3, 1): params["capacity_3_1"],
        (3, 2): params["capacity_3_2"],
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.commodities = pyo.Set(initialize=commodities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.facility_arcs = pyo.Set(
        dimen=2, initialize=facility_arcs, ordered=True
    )
    model.costed_flows = pyo.Set(
        dimen=3, initialize=tuple(transport_costs), ordered=True
    )

    model.transport_cost = pyo.Param(
        model.costed_flows, initialize=transport_costs, within=pyo.Reals
    )
    model.install_cost = pyo.Param(
        model.facility_arcs, initialize=installation_costs, within=pyo.Reals
    )
    model.route_capacity = pyo.Param(
        model.facility_arcs, initialize=capacities, within=pyo.Reals
    )

    model.flow = pyo.Var(
        model.commodities,
        model.arcs,
        domain=pyo.NonNegativeReals,
        bounds=(0, 1),
    )
    model.facilities = pyo.Var(
        model.facility_arcs, domain=pyo.NonNegativeIntegers
    )

    def flow_balance_rule(network, commodity, node):
        outgoing = sum(
            network.flow[commodity, tail, head]
            for tail, head in arcs
            if tail == node
        )
        incoming = sum(
            network.flow[commodity, tail, head]
            for tail, head in arcs
            if head == node
        )
        net_supply = (
            1 if node == origins[commodity]
            else -1 if node == destinations[commodity]
            else 0
        )
        return outgoing - incoming == net_supply

    model.flow_balance = pyo.Constraint(
        model.commodities, model.nodes, rule=flow_balance_rule
    )

    def capacity_rule(network, tail, head):
        return (
            sum(
                network.flow[commodity, tail, head]
                for commodity in commodities
            )
            <= network.route_capacity[tail, head]
            * network.facilities[tail, head]
        )

    model.capacity_limits = pyo.Constraint(
        model.facility_arcs, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[commodity, tail, head]
            * model.flow[commodity, tail, head]
            for commodity, tail, head in model.costed_flows
        )
        + sum(
            model.install_cost[tail, head] * model.facilities[tail, head]
            for tail, head in facility_arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Routes with transport costs per commodity
    # (i, j, commodity_index): cost
    transport_routes = {
        (0, 3, 1): params["transport_cost_c1_0_3"],
        (0, 1, 1): params["transport_cost_c1_0_1"],
        (0, 2, 1): params["transport_cost_c1_0_2"],
        (1, 2, 2): params["transport_cost_c2_1_2"],
        (1, 3, 2): params["transport_cost_c2_1_3"],
    }

    # Routes with facility installation
    facility_routes = {
        (0, 3): (params["install_cost_0_3"], params["capacity_0_3"]),
        (1, 2): (params["install_cost_1_2"], params["capacity_1_2"]),
        (1, 3): (params["install_cost_1_3"], params["capacity_1_3"]),
        (2, 0): (params["install_cost_2_0"], params["capacity_2_0"]),
        (2, 1): (params["install_cost_2_1"], params["capacity_2_1"]),
        (3, 1): (params["install_cost_3_1"], params["capacity_3_1"]),
        (3, 2): (params["install_cost_3_2"], params["capacity_3_2"]),
    }

    # Commodity definitions: (origin, destination)
    commodities = {1: (0, 3), 2: (1, 2)}

    # All arcs per commodity (from transport_routes)
    arcs_per_commodity = {k: [] for k in commodities}
    for (i, j, k) in transport_routes:
        arcs_per_commodity[k].append((i, j))

    # All nodes
    nodes = set(range(4))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Flow variables: f[i,j,k] in [0,1]
    flow = {}
    for (i, j, k), cost in transport_routes.items():
        flow[(i, j, k)] = model.addVar(lb=0.0, ub=1.0, vtype=GRB.CONTINUOUS,
                                        name=f"flow_{i}_{j}_{k}")

    # Facility variables: y[i,j] >= 0 integer
    facility = {}
    for (i, j) in facility_routes:
        facility[(i, j)] = model.addVar(lb=0, vtype=GRB.INTEGER,
                                         name=f"facility_{i}_{j}")

    # Objective: minimize transport costs + installation costs
    obj = gp.LinExpr()
    for (i, j, k), cost in transport_routes.items():
        obj += cost * flow[(i, j, k)]
    for (i, j), (inst_cost, cap) in facility_routes.items():
        obj += inst_cost * facility[(i, j)]
    model.setObjective(obj, GRB.MINIMIZE)

    # Flow conservation constraints
    # For each commodity k with origin o and destination d:
    #   sum of flow out of node n - sum of flow into node n = supply[n]
    #   supply[o] = 1, supply[d] = -1, supply[others] = 0
    for k, (origin, dest) in commodities.items():
        for node in nodes:
            out_flow = gp.LinExpr()
            in_flow = gp.LinExpr()
            for (i, j, kk) in transport_routes:
                if kk != k:
                    continue
                if i == node:
                    out_flow += flow[(i, j, k)]
                if j == node:
                    in_flow += flow[(i, j, k)]
            if node == origin:
                supply = 1.0
            elif node == dest:
                supply = -1.0
            else:
                supply = 0.0
            # Only add constraint if node appears in any arc for this commodity
            # (avoids trivial 0=0 constraints, but harmless to include)
            model.addConstr(out_flow - in_flow == supply,
                            name=f"flow_conservation_k{k}_n{node}")

    # Capacity constraints: total flow on route (i,j) <= capacity * facilities installed
    # Group flow variables by arc (i,j) across all commodities
    arc_flows = {}
    for (i, j, k) in transport_routes:
        arc = (i, j)
        if arc not in arc_flows:
            arc_flows[arc] = gp.LinExpr()
        arc_flows[arc] += flow[(i, j, k)]

    for (i, j), (inst_cost, cap) in facility_routes.items():
        total_flow = arc_flows.get((i, j), gp.LinExpr())
        model.addConstr(total_flow <= cap * facility[(i, j)],
                        name=f"capacity_{i}_{j}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}
```

### 6. Objective values

Rules that certify it: gate, panel_base_2of3, ind_gate.

#### param_screen

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 1844.0 (optimal) | 1839.0 (optimal) | 1844.0 (optimal) |
| 1 | 1652.1326826488714 (optimal) | 1026.8572939689873 (optimal) | 1652.1326826488714 (optimal) |
| 2 | 1938.7739804117293 (optimal) | 1830.9351175607915 (optimal) | 1938.7739804117293 (optimal) |
| 3 | 1418.2678614857189 (optimal) | 1405.5644983894135 (optimal) | 1418.2678614857186 (optimal) |
| 4 | 2185.609260935708 (optimal) | 1845.4569939762912 (optimal) | 2185.609260935708 (optimal) |
| 5 | 1957.748726978301 (optimal) | 1605.8573394173598 (optimal) | 1957.748726978301 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 1844.0 (optimal) | 1839.0 (optimal) | 1844.0 (optimal) |
| 1 | 1652.1326826488714 (optimal) | 1026.8572939689873 (optimal) | 1652.1326826488714 (optimal) |
| 2 | 1938.7739804117293 (optimal) | 1830.9351175607915 (optimal) | 1938.7739804117293 (optimal) |
| 3 | 1418.2678614857189 (optimal) | 1405.5644983894135 (optimal) | 1418.2678614857186 (optimal) |
| 4 | 2185.609260935708 (optimal) | 1845.4569939762912 (optimal) | 2185.609260935708 (optimal) |
| 5 | 1957.748726978301 (optimal) | 1605.8573394173598 (optimal) | 1957.748726978301 (optimal) |

