# PySpark Methods Reference

## Table of Contents
- [SparkSession](#sparksession)
- [DataFrame Creation](#dataframe-creation)
- [DataFrame Actions](#dataframe-actions)
- [DataFrame Transformations](#dataframe-transformations)
- [Column Operations](#column-operations)
- [Aggregation Functions](#aggregation-functions)
- [Window Functions](#window-functions)
- [Join Operations](#join-operations)
- [I/O (Reading & Writing)](#io-reading--writing)
- [SQL Functions (pyspark.sql.functions)](#sql-functions)
- [String Functions](#string-functions)
- [Date & Time Functions](#date--time-functions)
- [Math Functions](#math-functions)
- [Null Handling](#null-handling)
- [Schema & Types](#schema--types)
- [UDFs (User Defined Functions)](#udfs-user-defined-functions)
- [RDD Operations](#rdd-operations)
- [Spark Streaming (Structured)](#spark-streaming-structured)
- [Configuration & Performance](#configuration--performance)

---

## SparkSession

### Creating a Session
```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("MyApp") \
    .master("local[*]") \
    .config("spark.some.config.option", "value") \
    .enableHiveSupport() \
    .getOrCreate()
```

### Key SparkSession Methods
| Method | Description |
|---|---|
| `spark.sql(query)` | Execute a SQL query, returns DataFrame |
| `spark.table(tableName)` | Returns the specified table as a DataFrame |
| `spark.catalog` | Access the catalog interface (databases, tables, functions) |
| `spark.conf.set(key, value)` | Set a runtime config option |
| `spark.conf.get(key)` | Get a runtime config value |
| `spark.createDataFrame(data, schema)` | Create a DataFrame from data |
| `spark.range(start, end, step)` | Create a DataFrame with a single `id` column |
| `spark.read` | Returns a DataFrameReader |
| `spark.readStream` | Returns a DataStreamReader |
| `spark.stop()` | Stop the SparkSession |
| `spark.newSession()` | Create a new SparkSession with isolated SQL configs |
| `spark.sparkContext` | Access the underlying SparkContext |
| `spark.version` | Get the Spark version string |
| `spark.udf.register(name, f, returnType)` | Register a UDF for SQL use |

### Catalog Methods
```python
spark.catalog.listDatabases()
spark.catalog.listTables(dbName=None)
spark.catalog.listColumns(tableName, dbName=None)
spark.catalog.listFunctions(dbName=None)
spark.catalog.tableExists(tableName, dbName=None)
spark.catalog.isCached(tableName)
spark.catalog.cacheTable(tableName)
spark.catalog.uncacheTable(tableName)
spark.catalog.clearCache()
spark.catalog.refreshTable(tableName)
spark.catalog.createExternalTable(tableName, path, source, schema)
spark.catalog.dropTempView(viewName)
spark.catalog.dropGlobalTempView(viewName)
spark.catalog.setCurrentDatabase(dbName)
spark.catalog.currentDatabase()
```

---

## DataFrame Creation

### From Collections
```python
# From list of tuples
data = [("Alice", 25), ("Bob", 30)]
df = spark.createDataFrame(data, ["name", "age"])

# From list of Row objects
from pyspark.sql import Row
rows = [Row(name="Alice", age=25), Row(name="Bob", age=30)]
df = spark.createDataFrame(rows)

# From list of dicts
data = [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]
df = spark.createDataFrame(data)

# With explicit schema
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
schema = StructType([
    StructField("name", StringType(), True),
    StructField("age", IntegerType(), True)
])
df = spark.createDataFrame(data, schema)

# From pandas DataFrame
import pandas as pd
pdf = pd.DataFrame({"name": ["Alice", "Bob"], "age": [25, 30]})
df = spark.createDataFrame(pdf)
```

### From range
```python
df = spark.range(0, 100, 1)           # id column from 0 to 99
df = spark.range(10)                   # id column from 0 to 9
df = spark.range(0, 100, 2, numPartitions=4)
```

### From RDD
```python
rdd = spark.sparkContext.parallelize([("Alice", 25), ("Bob", 30)])
df = rdd.toDF(["name", "age"])
df = spark.createDataFrame(rdd, schema)
```

---

## DataFrame Actions

Actions trigger computation and return results.

| Method | Description |
|---|---|
| `df.show(n=20, truncate=True, vertical=False)` | Print first n rows |
| `df.collect()` | Return all rows as a list of Row objects |
| `df.take(n)` | Return first n rows as a list |
| `df.first()` | Return the first row |
| `df.head(n=1)` | Return the first n rows |
| `df.tail(n)` | Return the last n rows |
| `df.count()` | Return the number of rows |
| `df.describe(*cols)` | Compute summary statistics |
| `df.summary(*statistics)` | Compute specified statistics (e.g., "count", "mean", "25%") |
| `df.toPandas()` | Convert to pandas DataFrame |
| `df.toLocalIterator()` | Return an iterator of Row objects |
| `df.foreach(f)` | Apply function f to each row |
| `df.foreachPartition(f)` | Apply function f to each partition |
| `df.isEmpty()` | Returns True if the DataFrame is empty |

### Examples
```python
df.show(5, truncate=False)
df.show(vertical=True)

rows = df.collect()
for row in rows:
    print(row["name"], row["age"])

print(df.count())
df.describe("age", "salary").show()
df.summary("count", "min", "max", "mean", "stddev").show()
```

---

## DataFrame Transformations

Transformations return a new DataFrame (lazy evaluation).

### Selection & Projection
| Method | Description |
|---|---|
| `df.select(*cols)` | Select columns |
| `df.selectExpr(*expr)` | Select with SQL expressions |
| `df.withColumn(name, col)` | Add or replace a column |
| `df.withColumns(colsMap)` | Add or replace multiple columns (Spark 3.3+) |
| `df.withColumnRenamed(existing, new)` | Rename a column |
| `df.withColumnsRenamed(colsMap)` | Rename multiple columns (Spark 3.4+) |
| `df.drop(*cols)` | Drop columns |
| `df.alias(name)` | Return DataFrame with an alias |
| `df.toDF(*cols)` | Return DataFrame with renamed columns |

```python
df.select("name", "age")
df.select(df.name, df.age + 1)
df.select(col("name"), col("age").alias("years"))
df.selectExpr("name", "age + 1 as age_next_year")

df.withColumn("age_doubled", col("age") * 2)
df.withColumns({"age_doubled": col("age") * 2, "name_upper": upper(col("name"))})
df.withColumnRenamed("name", "full_name")
df.drop("age")
```

### Filtering
| Method | Description |
|---|---|
| `df.filter(condition)` | Filter rows |
| `df.where(condition)` | Alias for filter |

```python
df.filter(col("age") > 25)
df.filter("age > 25")
df.filter((col("age") > 25) & (col("name") != "Bob"))
df.where(col("name").like("A%"))
df.where(col("name").isin(["Alice", "Bob"]))
df.where(col("name").isNotNull())
df.where(col("age").between(20, 30))
```

### Sorting
| Method | Description |
|---|---|
| `df.sort(*cols, **kwargs)` | Sort by columns |
| `df.orderBy(*cols, **kwargs)` | Alias for sort |
| `df.sortWithinPartitions(*cols)` | Sort within each partition |

```python
df.sort("age")
df.sort(col("age").desc())
df.sort("name", ascending=False)
df.orderBy(col("age").asc(), col("name").desc())
df.orderBy(col("age").asc_nulls_first())
df.orderBy(col("age").desc_nulls_last())
```

### Distinct & Deduplication
| Method | Description |
|---|---|
| `df.distinct()` | Return distinct rows |
| `df.dropDuplicates(subset=None)` | Drop duplicate rows |
| `df.dropDuplicatesWithinWatermark(subset)` | Drop duplicates within watermark (streaming) |

```python
df.distinct()
df.dropDuplicates()
df.dropDuplicates(["name"])
```

### Limiting & Sampling
| Method | Description |
|---|---|
| `df.limit(n)` | Return first n rows |
| `df.sample(fraction, seed=None)` | Return a random sample |
| `df.sampleBy(col, fractions, seed)` | Stratified sample |
| `df.randomSplit(weights, seed)` | Split into multiple DataFrames |

```python
df.limit(10)
df.sample(0.5, seed=42)
df.sample(withReplacement=True, fraction=0.5)
df.sampleBy("label", fractions={0: 0.1, 1: 0.2}, seed=42)
train, test = df.randomSplit([0.8, 0.2], seed=42)
```

### Set Operations
| Method | Description |
|---|---|
| `df1.union(df2)` | Union (keeps duplicates) |
| `df1.unionAll(df2)` | Alias for union |
| `df1.unionByName(df2, allowMissingColumns=False)` | Union by column name |
| `df1.intersect(df2)` | Intersection (distinct) |
| `df1.intersectAll(df2)` | Intersection (keeps duplicates) |
| `df1.subtract(df2)` | Set difference (distinct) |
| `df1.exceptAll(df2)` | Set difference (keeps duplicates) |

### Grouping & Aggregation
| Method | Description |
|---|---|
| `df.groupBy(*cols)` | Group by columns |
| `df.groupby(*cols)` | Alias for groupBy |
| `df.rollup(*cols)` | Create a rollup |
| `df.cube(*cols)` | Create a cube |
| `df.pivot(col, values=None)` | Pivot after groupBy |
| `df.agg(*exprs)` | Aggregate without grouping |
| `df.unpivot(ids, values, variableColumnName, valueColumnName)` | Unpivot (Spark 3.4+) |

```python
df.groupBy("department").count()
df.groupBy("department").agg(
    avg("salary").alias("avg_salary"),
    max("salary").alias("max_salary"),
    min("salary").alias("min_salary"),
    sum("salary").alias("total_salary"),
    count("*").alias("num_employees")
)
df.groupBy("department").pivot("year").sum("revenue")
df.groupBy("department").pivot("year", [2020, 2021, 2022]).sum("revenue")

df.rollup("department", "year").sum("revenue").show()
df.cube("department", "year").sum("revenue").show()
```

### Repartitioning
| Method | Description |
|---|---|
| `df.repartition(numPartitions, *cols)` | Repartition (full shuffle) |
| `df.repartitionByRange(numPartitions, *cols)` | Range-based repartition |
| `df.coalesce(numPartitions)` | Reduce partitions (no shuffle) |

```python
df.repartition(10)
df.repartition(10, "department")
df.repartitionByRange(10, col("age"))
df.coalesce(1)
```

### Caching & Persistence
| Method | Description |
|---|---|
| `df.cache()` | Cache in memory (MEMORY_AND_DISK) |
| `df.persist(storageLevel)` | Persist with specific storage level |
| `df.unpersist(blocking=False)` | Remove from cache |
| `df.storageLevel` | Get current storage level |
| `df.is_cached` | Whether the DataFrame is cached |

```python
from pyspark import StorageLevel
df.cache()
df.persist(StorageLevel.MEMORY_AND_DISK)
df.persist(StorageLevel.DISK_ONLY)
df.persist(StorageLevel.MEMORY_ONLY)
df.unpersist()
```

### Temp Views
| Method | Description |
|---|---|
| `df.createOrReplaceTempView(name)` | Register as temp view |
| `df.createTempView(name)` | Register as temp view (fails if exists) |
| `df.createOrReplaceGlobalTempView(name)` | Register as global temp view |
| `df.createGlobalTempView(name)` | Register as global temp view (fails if exists) |

```python
df.createOrReplaceTempView("people")
result = spark.sql("SELECT * FROM people WHERE age > 25")

df.createOrReplaceGlobalTempView("people")
result = spark.sql("SELECT * FROM global_temp.people")
```

### Miscellaneous Transformations
| Method | Description |
|---|---|
| `df.transform(func)` | Apply a function that takes and returns a DataFrame |
| `df.hint(name, *params)` | Add an optimizer hint |
| `df.checkpoint(eager=True)` | Checkpoint the DataFrame |
| `df.localCheckpoint(eager=True)` | Local checkpoint |
| `df.crossJoin(other)` | Cartesian product |
| `df.observe(observation, *exprs)` | Collect metrics during query execution |
| `df.withWatermark(eventTime, delayThreshold)` | Define watermark (streaming) |
| `df.withMetadata(columnName, metadata)` | Attach metadata to a column |

```python
def add_greeting(df):
    return df.withColumn("greeting", concat(lit("Hello, "), col("name")))

df.transform(add_greeting)
df.hint("broadcast")
```

---

## Column Operations

### Creating Column References
```python
from pyspark.sql.functions import col, lit, expr

col("name")          # Reference column by name
df["name"]           # Reference column by name
df.name              # Reference column by attribute

lit(42)              # Literal value
expr("age + 1")      # SQL expression
```

### Column Methods
| Method | Description |
|---|---|
| `col.alias(name)` | Rename column |
| `col.name(name)` | Alias for alias |
| `col.cast(dataType)` | Cast to another type |
| `col.astype(dataType)` | Alias for cast |
| `col.asc()` | Ascending sort |
| `col.asc_nulls_first()` | Ascending, nulls first |
| `col.asc_nulls_last()` | Ascending, nulls last |
| `col.desc()` | Descending sort |
| `col.desc_nulls_first()` | Descending, nulls first |
| `col.desc_nulls_last()` | Descending, nulls last |
| `col.isNull()` | Is null |
| `col.isNotNull()` | Is not null |
| `col.isNaN()` | Is NaN |
| `col.isin(*vals)` | Is in list |
| `col.like(pattern)` | SQL LIKE |
| `col.rlike(pattern)` | Regex match |
| `col.startswith(prefix)` | Starts with |
| `col.endswith(suffix)` | Ends with |
| `col.contains(string)` | Contains substring |
| `col.between(lower, upper)` | Between (inclusive) |
| `col.when(condition, value)` | Conditional |
| `col.otherwise(value)` | Default for when |
| `col.over(window)` | Apply over a window |
| `col.substr(start, length)` | Substring |
| `col.getItem(key)` | Get item from array/map |
| `col.getField(name)` | Get field from struct |
| `col.dropFields(*fieldNames)` | Drop fields from struct |
| `col.withField(fieldName, col)` | Add/replace field in struct |
| `col.eqNullSafe(other)` | Null-safe equality |
| `col.bitwiseAND(other)` | Bitwise AND |
| `col.bitwiseOR(other)` | Bitwise OR |
| `col.bitwiseXOR(other)` | Bitwise XOR |

### Arithmetic Operators
```python
col("a") + col("b")   # Addition
col("a") - col("b")   # Subtraction
col("a") * col("b")   # Multiplication
col("a") / col("b")   # Division
col("a") % col("b")   # Modulo
col("a") ** 2          # Power
-col("a")              # Negation
```

### Comparison Operators
```python
col("a") == col("b")
col("a") != col("b")
col("a") > col("b")
col("a") >= col("b")
col("a") < col("b")
col("a") <= col("b")
```

### Logical Operators
```python
(col("a") > 1) & (col("b") < 10)   # AND
(col("a") > 1) | (col("b") < 10)   # OR
~(col("a") > 1)                      # NOT
```

---

## Aggregation Functions

```python
from pyspark.sql.functions import (
    count, countDistinct, approx_count_distinct,
    sum, sumDistinct, avg, mean,
    min, max, first, last,
    stddev, stddev_pop, stddev_samp,
    variance, var_pop, var_samp,
    skewness, kurtosis,
    collect_list, collect_set,
    grouping, grouping_id,
    percentile_approx, covar_pop, covar_samp, corr
)
```

| Function | Description |
|---|---|
| `count(col)` | Count non-null values |
| `count("*")` | Count all rows |
| `countDistinct(col, *cols)` | Count distinct values |
| `approx_count_distinct(col, rsd=0.05)` | Approximate distinct count |
| `sum(col)` | Sum |
| `sumDistinct(col)` | Sum of distinct values |
| `avg(col)` / `mean(col)` | Average |
| `min(col)` | Minimum |
| `max(col)` | Maximum |
| `first(col, ignorenulls=False)` | First value |
| `last(col, ignorenulls=False)` | Last value |
| `stddev(col)` / `stddev_samp(col)` | Sample standard deviation |
| `stddev_pop(col)` | Population standard deviation |
| `variance(col)` / `var_samp(col)` | Sample variance |
| `var_pop(col)` | Population variance |
| `skewness(col)` | Skewness |
| `kurtosis(col)` | Kurtosis |
| `collect_list(col)` | Collect values into a list (with duplicates) |
| `collect_set(col)` | Collect values into a set (no duplicates) |
| `percentile_approx(col, percentage, accuracy)` | Approximate percentile |
| `covar_pop(col1, col2)` | Population covariance |
| `covar_samp(col1, col2)` | Sample covariance |
| `corr(col1, col2)` | Pearson correlation |

### GroupedData Methods
After `df.groupBy(...)`:

| Method | Description |
|---|---|
| `.count()` | Count per group |
| `.sum(*cols)` | Sum per group |
| `.avg(*cols)` / `.mean(*cols)` | Average per group |
| `.min(*cols)` | Min per group |
| `.max(*cols)` | Max per group |
| `.agg(*exprs)` | Custom aggregations |
| `.pivot(col, values)` | Pivot |
| `.apply(udf)` | Apply a grouped map UDF |
| `.applyInPandas(func, schema)` | Apply a pandas UDF per group |
| `.cogroup(other)` | Co-group with another GroupedData |

---

## Window Functions

```python
from pyspark.sql.window import Window
from pyspark.sql.functions import (
    row_number, rank, dense_rank, percent_rank,
    ntile, lag, lead,
    cume_dist, nth_value
)
```

### Defining Windows
```python
# Basic window
w = Window.partitionBy("department").orderBy("salary")

# With frame specification
w_rows = Window.partitionBy("department").orderBy("salary") \
    .rowsBetween(Window.unboundedPreceding, Window.currentRow)

w_range = Window.partitionBy("department").orderBy("salary") \
    .rangeBetween(Window.unboundedPreceding, 0)

# No partition (entire DataFrame)
w_all = Window.orderBy("salary")

# Frame boundaries
Window.unboundedPreceding   # -sys.maxsize
Window.unboundedFollowing   #  sys.maxsize
Window.currentRow           #  0
```

### Ranking Functions
| Function | Description |
|---|---|
| `row_number().over(w)` | Sequential row number (1, 2, 3, ...) |
| `rank().over(w)` | Rank with gaps (1, 2, 2, 4) |
| `dense_rank().over(w)` | Rank without gaps (1, 2, 2, 3) |
| `percent_rank().over(w)` | Relative rank (0.0 to 1.0) |
| `ntile(n).over(w)` | Divide into n buckets |
| `cume_dist().over(w)` | Cumulative distribution |

### Analytical Functions
| Function | Description |
|---|---|
| `lag(col, offset=1, default=None).over(w)` | Value from previous row |
| `lead(col, offset=1, default=None).over(w)` | Value from next row |
| `nth_value(col, n).over(w)` | Nth value in the window |

### Aggregate Functions Over Windows
```python
df.withColumn("running_sum", sum("salary").over(w_rows))
df.withColumn("dept_avg", avg("salary").over(Window.partitionBy("department")))
df.withColumn("dept_max", max("salary").over(Window.partitionBy("department")))
df.withColumn("dept_count", count("*").over(Window.partitionBy("department")))
```

### Complete Example
```python
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number, rank, dense_rank, lag, lead, sum, avg

w = Window.partitionBy("department").orderBy(col("salary").desc())

df.withColumn("row_num", row_number().over(w)) \
  .withColumn("rank", rank().over(w)) \
  .withColumn("dense_rank", dense_rank().over(w)) \
  .withColumn("prev_salary", lag("salary", 1).over(w)) \
  .withColumn("next_salary", lead("salary", 1).over(w)) \
  .withColumn("running_total", sum("salary").over(
      Window.partitionBy("department").orderBy("salary").rowsBetween(
          Window.unboundedPreceding, Window.currentRow
      )
  ))
```

---

## Join Operations

### Join Types
```python
# Inner join (default)
df1.join(df2, "key")
df1.join(df2, df1.key == df2.key)
df1.join(df2, ["key1", "key2"])

# Left outer join
df1.join(df2, "key", "left")
df1.join(df2, "key", "left_outer")

# Right outer join
df1.join(df2, "key", "right")
df1.join(df2, "key", "right_outer")

# Full outer join
df1.join(df2, "key", "outer")
df1.join(df2, "key", "full")
df1.join(df2, "key", "full_outer")

# Left semi join (rows in df1 that have match in df2)
df1.join(df2, "key", "left_semi")

# Left anti join (rows in df1 that do NOT have match in df2)
df1.join(df2, "key", "left_anti")

# Cross join
df1.crossJoin(df2)
df1.join(df2, how="cross")
```

### Join Hints
```python
df1.join(df2.hint("broadcast"), "key")   # Broadcast join
df1.hint("merge").join(df2, "key")       # Sort-merge join
df1.hint("shuffle_hash").join(df2, "key") # Shuffle hash join
df1.hint("shuffle_replicate_nl").join(df2, "key") # Nested loop join
```

### Handling Duplicate Column Names
```python
# Using aliases
a = df1.alias("a")
b = df2.alias("b")
result = a.join(b, col("a.key") == col("b.key")).select("a.*", "b.value")

# Drop duplicate column after join
result = df1.join(df2, df1.key == df2.key).drop(df2.key)
```

---

## I/O (Reading & Writing)

### Reading Data
```python
# CSV
df = spark.read.csv("path/to/file.csv", header=True, inferSchema=True)
df = spark.read.option("header", True).option("inferSchema", True).csv("path.csv")
df = spark.read.options(header=True, inferSchema=True, sep=",").csv("path.csv")
df = spark.read.csv("path.csv", header=True, inferSchema=True, 
                     nullValue="NA", dateFormat="yyyy-MM-dd",
                     multiLine=True, encoding="UTF-8",
                     quote='"', escape="\\", comment="#")

# JSON
df = spark.read.json("path/to/file.json")
df = spark.read.json("path.json", multiLine=True)
df = spark.read.option("multiLine", True).json("path.json")

# Parquet
df = spark.read.parquet("path/to/file.parquet")
df = spark.read.parquet("path1", "path2")  # Multiple paths

# ORC
df = spark.read.orc("path/to/file.orc")

# Avro
df = spark.read.format("avro").load("path/to/file.avro")

# Delta (requires delta-spark)
df = spark.read.format("delta").load("path/to/delta_table")

# Text
df = spark.read.text("path/to/file.txt")
df = spark.read.text("path.txt", wholetext=True)

# JDBC
df = spark.read.jdbc(
    url="jdbc:postgresql://host:5432/db",
    table="schema.table",
    properties={"user": "usr", "password": "pwd", "driver": "org.postgresql.Driver"}
)

# With explicit schema
df = spark.read.schema(schema).csv("path.csv")

# Generic format
df = spark.read.format("csv").option("header", True).load("path.csv")
df = spark.read.load("path.parquet", format="parquet")
```

### DataFrameReader Options (CSV)
| Option | Description |
|---|---|
| `header` | First row as header (default: false) |
| `inferSchema` | Infer data types (default: false) |
| `sep` / `delimiter` | Column delimiter (default: `,`) |
| `quote` | Quote character (default: `"`) |
| `escape` | Escape character (default: `\`) |
| `comment` | Comment character |
| `multiLine` | Allow multi-line values (default: false) |
| `encoding` | File encoding (default: UTF-8) |
| `nullValue` | String representation of null |
| `nanValue` | String representation of NaN |
| `dateFormat` | Date format pattern |
| `timestampFormat` | Timestamp format pattern |
| `mode` | Parse mode: PERMISSIVE, DROPMALFORMED, FAILFAST |
| `columnNameOfCorruptRecord` | Column for corrupt records |
| `emptyValue` | String representation of empty value |
| `lineSep` | Line separator |
| `pathGlobFilter` | Glob pattern for file filtering |
| `recursiveFileLookup` | Read files recursively |
| `maxColumns` | Maximum number of columns |

### Writing Data
```python
# CSV
df.write.csv("output/path", header=True, mode="overwrite")

# JSON
df.write.json("output/path", mode="overwrite")

# Parquet
df.write.parquet("output/path", mode="overwrite")

# ORC
df.write.orc("output/path", mode="overwrite")

# Single file output
df.coalesce(1).write.csv("output/path", header=True)

# Partitioned output
df.write.partitionBy("year", "month").parquet("output/path")

# Bucketed output (saveAsTable only)
df.write.bucketBy(10, "key").sortBy("value").saveAsTable("table_name")

# Save as table
df.write.saveAsTable("table_name")

# Insert into existing table
df.write.insertInto("table_name")

# JDBC
df.write.jdbc(
    url="jdbc:postgresql://host:5432/db",
    table="schema.table",
    mode="overwrite",
    properties={"user": "usr", "password": "pwd", "driver": "org.postgresql.Driver"}
)

# Generic format
df.write.format("csv").option("header", True).save("output/path")
```

### Write Modes
| Mode | Description |
|---|---|
| `"overwrite"` | Overwrite existing data |
| `"append"` | Append to existing data |
| `"ignore"` | Silently skip if data exists |
| `"error"` / `"errorifexists"` | Throw error if data exists (default) |

### DataFrameWriter Methods
| Method | Description |
|---|---|
| `.mode(saveMode)` | Set save mode |
| `.format(source)` | Set data format |
| `.option(key, value)` | Set a single option |
| `.options(**kwargs)` | Set multiple options |
| `.partitionBy(*cols)` | Partition output by columns |
| `.bucketBy(numBuckets, col, *cols)` | Bucket output |
| `.sortBy(*cols)` | Sort within buckets |
| `.save(path)` | Save to path |
| `.saveAsTable(name)` | Save as managed table |
| `.insertInto(tableName)` | Insert into table |

---

## SQL Functions

```python
from pyspark.sql.functions import *
```

### General Functions
| Function | Description |
|---|---|
| `col(name)` | Reference a column |
| `lit(value)` | Literal value |
| `expr(str)` | SQL expression |
| `when(condition, value)` | Conditional (use with `.otherwise()`) |
| `coalesce(*cols)` | First non-null value |
| `greatest(*cols)` | Greatest value across columns |
| `least(*cols)` | Least value across columns |
| `isnull(col)` | Check if null |
| `isnan(col)` | Check if NaN |
| `nanvl(col1, col2)` | Return col2 if col1 is NaN |
| `hash(*cols)` | Hash of columns |
| `xxhash64(*cols)` | 64-bit hash |
| `md5(col)` | MD5 hash |
| `sha1(col)` | SHA-1 hash |
| `sha2(col, numBits)` | SHA-2 hash |
| `crc32(col)` | CRC32 checksum |
| `monotonically_increasing_id()` | Monotonically increasing 64-bit ID |
| `spark_partition_id()` | Partition ID |
| `input_file_name()` | Name of current input file |
| `struct(*cols)` | Create a struct |
| `named_struct(*cols)` | Create a named struct |
| `typedLit(value)` | Typed literal (supports complex types) |
| `broadcast(df)` | Broadcast hint for joins |

### Conditional Logic
```python
from pyspark.sql.functions import when, col

df.withColumn("category",
    when(col("age") < 18, "minor")
    .when(col("age") < 65, "adult")
    .otherwise("senior")
)

# CASE WHEN via expr
df.withColumn("category",
    expr("CASE WHEN age < 18 THEN 'minor' WHEN age < 65 THEN 'adult' ELSE 'senior' END")
)
```

---

## String Functions

```python
from pyspark.sql.functions import (
    upper, lower, initcap,
    trim, ltrim, rtrim,
    lpad, rpad,
    length, char_length, bit_length, octet_length,
    concat, concat_ws,
    substring, substr,
    split, regexp_extract, regexp_replace,
    translate, overlay,
    instr, locate,
    repeat, reverse,
    ascii, chr, base64, unbase64,
    encode, decode,
    format_string,
    soundex, levenshtein,
    left, right
)
```

| Function | Description |
|---|---|
| `upper(col)` | Uppercase |
| `lower(col)` | Lowercase |
| `initcap(col)` | Capitalize first letter of each word |
| `trim(col)` | Trim whitespace |
| `ltrim(col)` | Left trim |
| `rtrim(col)` | Right trim |
| `lpad(col, len, pad)` | Left pad |
| `rpad(col, len, pad)` | Right pad |
| `length(col)` | String length |
| `concat(*cols)` | Concatenate strings |
| `concat_ws(sep, *cols)` | Concatenate with separator |
| `substring(col, pos, len)` | Substring (1-indexed) |
| `split(col, pattern, limit=-1)` | Split string into array |
| `regexp_extract(col, pattern, idx)` | Extract regex group |
| `regexp_replace(col, pattern, replacement)` | Regex replace |
| `translate(col, matching, replace)` | Character-level translation |
| `overlay(src, replace, pos, len)` | Overlay string |
| `instr(col, substr)` | Position of substring (1-indexed, 0 if not found) |
| `locate(substr, col, pos=1)` | Position of substring |
| `repeat(col, n)` | Repeat string n times |
| `reverse(col)` | Reverse string |
| `ascii(col)` | ASCII value of first character |
| `format_string(format, *cols)` | Printf-style formatting |
| `soundex(col)` | Soundex code |
| `levenshtein(col1, col2)` | Levenshtein distance |
| `left(col, len)` | Left n characters |
| `right(col, len)` | Right n characters |

```python
df.withColumn("upper_name", upper(col("name")))
df.withColumn("email_domain", regexp_extract(col("email"), r"@(.+)", 1))
df.withColumn("words", split(col("sentence"), " "))
df.withColumn("full_name", concat_ws(" ", col("first"), col("last")))
```

---

## Date & Time Functions

```python
from pyspark.sql.functions import (
    current_date, current_timestamp,
    date_format, to_date, to_timestamp,
    year, quarter, month, dayofmonth, dayofweek, dayofyear,
    weekofyear, hour, minute, second,
    date_add, date_sub, datediff, months_between,
    add_months, last_day, next_day,
    date_trunc, trunc,
    from_unixtime, unix_timestamp,
    from_utc_timestamp, to_utc_timestamp,
    window, session_window,
    make_date, make_timestamp
)
```

| Function | Description |
|---|---|
| `current_date()` | Current date |
| `current_timestamp()` | Current timestamp |
| `date_format(col, fmt)` | Format date as string |
| `to_date(col, fmt=None)` | Convert to date |
| `to_timestamp(col, fmt=None)` | Convert to timestamp |
| `year(col)` | Extract year |
| `quarter(col)` | Extract quarter |
| `month(col)` | Extract month |
| `dayofmonth(col)` | Extract day of month |
| `dayofweek(col)` | Extract day of week (1=Sun, 7=Sat) |
| `dayofyear(col)` | Extract day of year |
| `weekofyear(col)` | Extract week of year |
| `hour(col)` | Extract hour |
| `minute(col)` | Extract minute |
| `second(col)` | Extract second |
| `date_add(col, days)` | Add days |
| `date_sub(col, days)` | Subtract days |
| `datediff(end, start)` | Difference in days |
| `months_between(end, start)` | Difference in months |
| `add_months(col, months)` | Add months |
| `last_day(col)` | Last day of month |
| `next_day(col, dayOfWeek)` | Next specified day of week |
| `date_trunc(fmt, col)` | Truncate to specified unit |
| `trunc(col, fmt)` | Truncate date |
| `from_unixtime(col, fmt)` | Unix timestamp to string |
| `unix_timestamp(col, fmt)` | String to Unix timestamp |
| `from_utc_timestamp(col, tz)` | UTC to given timezone |
| `to_utc_timestamp(col, tz)` | Given timezone to UTC |
| `make_date(year, month, day)` | Create date from parts |
| `make_timestamp(y, m, d, h, min, sec)` | Create timestamp from parts |

```python
df.withColumn("year", year(col("date")))
df.withColumn("formatted", date_format(col("ts"), "yyyy-MM-dd HH:mm:ss"))
df.withColumn("parsed", to_date(col("date_str"), "MM/dd/yyyy"))
df.withColumn("diff", datediff(col("end_date"), col("start_date")))
df.withColumn("next_month", add_months(col("date"), 1))
```

### Time Windows (Streaming & Batch)
```python
# Tumbling window
df.groupBy(window(col("timestamp"), "10 minutes")).count()

# Sliding window
df.groupBy(window(col("timestamp"), "10 minutes", "5 minutes")).count()

# Session window (Spark 3.2+)
df.groupBy(session_window(col("timestamp"), "10 minutes")).count()
```

---

## Math Functions

```python
from pyspark.sql.functions import (
    abs, ceil, floor, round, bround,
    sqrt, cbrt, pow, exp, expm1,
    log, log2, log10, log1p, ln,
    sin, cos, tan, asin, acos, atan, atan2,
    sinh, cosh, tanh,
    degrees, radians,
    factorial, signum,
    rand, randn,
    greatest, least,
    conv, hex, unhex,
    bin as bin_func
)
```

| Function | Description |
|---|---|
| `abs(col)` | Absolute value |
| `ceil(col)` / `ceiling(col)` | Ceiling |
| `floor(col)` | Floor |
| `round(col, scale=0)` | Round (half up) |
| `bround(col, scale=0)` | Banker's round (half even) |
| `sqrt(col)` | Square root |
| `cbrt(col)` | Cube root |
| `pow(col1, col2)` | Power |
| `exp(col)` | e^x |
| `log(arg1, arg2=None)` | Logarithm |
| `log2(col)` | Log base 2 |
| `log10(col)` | Log base 10 |
| `ln(col)` | Natural log |
| `factorial(col)` | Factorial |
| `rand(seed=None)` | Random uniform [0, 1) |
| `randn(seed=None)` | Random normal (mean=0, std=1) |
| `conv(col, fromBase, toBase)` | Base conversion |
| `hex(col)` | Hex string |
| `unhex(col)` | Inverse of hex |

---

## Null Handling

### Functions
| Function | Description |
|---|---|
| `coalesce(*cols)` | First non-null value |
| `isnull(col)` | True if null |
| `isnan(col)` | True if NaN |
| `nanvl(col1, col2)` | Return col2 if col1 is NaN |
| `ifnull(col1, col2)` | Return col2 if col1 is null |
| `nullif(col1, col2)` | Return null if col1 equals col2 |
| `nvl(col1, col2)` | Return col2 if col1 is null |
| `nvl2(col1, col2, col3)` | Return col2 if col1 is not null, else col3 |

### DataFrame Methods
| Method | Description |
|---|---|
| `df.na.drop(how="any", thresh=None, subset=None)` | Drop rows with nulls |
| `df.na.fill(value, subset=None)` | Fill nulls |
| `df.na.replace(to_replace, value, subset=None)` | Replace values |
| `df.dropna(how, thresh, subset)` | Alias for na.drop |
| `df.fillna(value, subset)` | Alias for na.fill |
| `df.replace(to_replace, value, subset)` | Alias for na.replace |

```python
# Drop rows where any column is null
df.na.drop("any")
# Drop rows where all columns are null
df.na.drop("all")
# Drop rows with nulls in specific columns
df.na.drop(subset=["age", "name"])
# Require at least 2 non-null values
df.na.drop(thresh=2)

# Fill nulls
df.na.fill(0)                          # Fill all numeric with 0
df.na.fill("unknown")                  # Fill all string with "unknown"
df.na.fill({"age": 0, "name": "N/A"}) # Fill specific columns

# Replace values
df.na.replace(["Alice", "Bob"], ["A", "B"], "name")
df.na.replace({25: 26, 30: 31})
```

---

## Schema & Types

### Data Types
```python
from pyspark.sql.types import (
    # Numeric
    ByteType, ShortType, IntegerType, LongType,
    FloatType, DoubleType, DecimalType,
    # String
    StringType, CharType, VarcharType,
    # Boolean
    BooleanType,
    # Binary
    BinaryType,
    # Date/Time
    DateType, TimestampType, TimestampNTZType,
    DayTimeIntervalType, YearMonthIntervalType,
    # Complex
    ArrayType, MapType, StructType, StructField,
    # Null
    NullType
)
```

### Defining Schemas
```python
schema = StructType([
    StructField("name", StringType(), nullable=True),
    StructField("age", IntegerType(), nullable=False),
    StructField("salary", DoubleType(), True),
    StructField("address", StructType([
        StructField("street", StringType(), True),
        StructField("city", StringType(), True),
        StructField("zip", StringType(), True)
    ]), True),
    StructField("scores", ArrayType(IntegerType()), True),
    StructField("properties", MapType(StringType(), StringType()), True)
])

# DDL string (simpler syntax)
schema = "name STRING, age INT, salary DOUBLE"
df = spark.read.schema(schema).csv("path.csv")
```

### Schema Inspection
| Method | Description |
|---|---|
| `df.schema` | Returns StructType schema |
| `df.printSchema()` | Print schema tree |
| `df.dtypes` | List of (column_name, type_string) tuples |
| `df.columns` | List of column names |
| `df.schema.fieldNames()` | List of field names |
| `df.schema.fields` | List of StructField objects |
| `df.schema.jsonValue()` | Schema as JSON |
| `df.schema.json()` | Schema as JSON string |
| `df.schema.simpleString()` | Compact schema string |
| `df.schema["name"].dataType` | Type of a specific field |

### Type Casting
```python
df.withColumn("age", col("age").cast(IntegerType()))
df.withColumn("age", col("age").cast("int"))
df.withColumn("date", col("date_str").cast("date"))
df.withColumn("ts", col("ts_str").cast("timestamp"))
df.select(col("*"), col("age").cast("double").alias("age_double"))
```

---

## Array & Map Functions

### Array Functions
```python
from pyspark.sql.functions import (
    array, array_contains, array_distinct, array_except,
    array_intersect, array_join, array_max, array_min,
    array_position, array_remove, array_repeat,
    array_sort, array_union, arrays_overlap, arrays_zip,
    element_at, explode, explode_outer,
    posexplode, posexplode_outer,
    flatten, sequence, shuffle, size, slice, sort_array,
    transform, filter, aggregate, exists, forall,
    zip_with, array_compact
)
```

| Function | Description |
|---|---|
| `array(*cols)` | Create array from columns |
| `array_contains(col, value)` | Check if array contains value |
| `array_distinct(col)` | Remove duplicates |
| `array_except(col1, col2)` | Set difference |
| `array_intersect(col1, col2)` | Set intersection |
| `array_union(col1, col2)` | Set union |
| `array_join(col, delimiter, null_replacement)` | Join array to string |
| `array_max(col)` | Max element |
| `array_min(col)` | Min element |
| `array_position(col, value)` | Position of value (1-indexed) |
| `array_remove(col, element)` | Remove all occurrences |
| `array_repeat(col, count)` | Repeat element |
| `array_sort(col)` | Sort array |
| `arrays_overlap(col1, col2)` | Check if arrays share elements |
| `arrays_zip(*cols)` | Zip arrays into array of structs |
| `element_at(col, index)` | Get element (1-indexed) |
| `explode(col)` | Expand array to rows |
| `explode_outer(col)` | Explode with nulls preserved |
| `posexplode(col)` | Explode with position index |
| `flatten(col)` | Flatten nested arrays |
| `sequence(start, stop, step)` | Generate sequence |
| `shuffle(col)` | Randomly shuffle array |
| `size(col)` | Array/map size |
| `slice(col, start, length)` | Slice array |
| `sort_array(col, asc=True)` | Sort array |
| `transform(col, f)` | Apply function to each element |
| `filter(col, f)` | Filter elements |
| `aggregate(col, zero, merge, finish)` | Reduce/fold array |
| `exists(col, f)` | Check if any element matches |
| `forall(col, f)` | Check if all elements match |
| `zip_with(col1, col2, f)` | Zip and apply function |

### Map Functions
```python
from pyspark.sql.functions import (
    create_map, map_keys, map_values, map_entries,
    map_from_arrays, map_from_entries,
    map_concat, map_filter, map_zip_with,
    element_at, size, transform_keys, transform_values
)
```

| Function | Description |
|---|---|
| `create_map(*cols)` | Create map from key-value pairs |
| `map_keys(col)` | Get all keys |
| `map_values(col)` | Get all values |
| `map_entries(col)` | Get array of key-value structs |
| `map_from_arrays(keys, values)` | Create map from key and value arrays |
| `map_from_entries(col)` | Create map from array of entries |
| `map_concat(*cols)` | Merge maps |
| `map_filter(col, f)` | Filter map entries |
| `map_zip_with(col1, col2, f)` | Zip two maps |
| `transform_keys(col, f)` | Transform map keys |
| `transform_values(col, f)` | Transform map values |
| `element_at(col, key)` | Get value by key |

---

## UDFs (User Defined Functions)

### Standard UDFs
```python
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType, IntegerType

# Method 1: Decorator
@udf(returnType=StringType())
def upper_udf(s):
    return s.upper() if s else None

# Method 2: Function
def add_one(x):
    return x + 1 if x else None

add_one_udf = udf(add_one, IntegerType())

# Usage
df.withColumn("upper_name", upper_udf(col("name")))
df.withColumn("age_plus_one", add_one_udf(col("age")))

# Register for SQL
spark.udf.register("upper_udf", lambda s: s.upper() if s else None, StringType())
spark.sql("SELECT upper_udf(name) FROM people")
```

### Pandas UDFs (Vectorized)
```python
from pyspark.sql.functions import pandas_udf
import pandas as pd

# Series to Series
@pandas_udf("double")
def multiply_by_two(s: pd.Series) -> pd.Series:
    return s * 2

# Series to Scalar (aggregation)
@pandas_udf("double")
def mean_udf(s: pd.Series) -> float:
    return s.mean()

# Iterator of Series to Iterator of Series
@pandas_udf("long")
def plus_one(iterator):
    for s in iterator:
        yield s + 1

# Usage
df.withColumn("doubled", multiply_by_two(col("value")))
df.groupBy("group").agg(mean_udf(col("value")))
```

### Grouped Map Pandas UDFs
```python
@pandas_udf(schema, PandasUDFType.GROUPED_MAP)
def normalize(pdf: pd.DataFrame) -> pd.DataFrame:
    pdf["normalized"] = (pdf["value"] - pdf["value"].mean()) / pdf["value"].std()
    return pdf

df.groupBy("group").applyInPandas(normalize, schema="group string, value double, normalized double")
```

---

## RDD Operations

### Creating RDDs
```python
sc = spark.sparkContext
rdd = sc.parallelize([1, 2, 3, 4, 5])
rdd = sc.textFile("path/to/file.txt")
rdd = sc.wholeTextFiles("path/to/dir")
rdd = df.rdd  # Convert DataFrame to RDD of Row objects
```

### RDD Transformations
| Method | Description |
|---|---|
| `rdd.map(f)` | Apply function to each element |
| `rdd.flatMap(f)` | Map then flatten |
| `rdd.filter(f)` | Filter elements |
| `rdd.distinct()` | Remove duplicates |
| `rdd.sample(withReplacement, fraction, seed)` | Sample |
| `rdd.union(other)` | Union |
| `rdd.intersection(other)` | Intersection |
| `rdd.subtract(other)` | Difference |
| `rdd.cartesian(other)` | Cartesian product |
| `rdd.groupBy(f)` | Group by function result |
| `rdd.sortBy(f, ascending=True)` | Sort by function result |
| `rdd.mapPartitions(f)` | Apply function to each partition |
| `rdd.mapPartitionsWithIndex(f)` | Map partitions with index |
| `rdd.repartition(n)` | Repartition |
| `rdd.coalesce(n)` | Reduce partitions |
| `rdd.zip(other)` | Zip two RDDs |
| `rdd.zipWithIndex()` | Zip with element index |
| `rdd.zipWithUniqueId()` | Zip with unique ID |
| `rdd.cache()` | Cache in memory |
| `rdd.persist(storageLevel)` | Persist |
| `rdd.unpersist()` | Remove from cache |

### Pair RDD Transformations
| Method | Description |
|---|---|
| `rdd.reduceByKey(f)` | Reduce values by key |
| `rdd.groupByKey()` | Group values by key |
| `rdd.sortByKey(ascending=True)` | Sort by key |
| `rdd.mapValues(f)` | Map values only |
| `rdd.flatMapValues(f)` | FlatMap values |
| `rdd.keys()` | Get keys |
| `rdd.values()` | Get values |
| `rdd.join(other)` | Inner join |
| `rdd.leftOuterJoin(other)` | Left outer join |
| `rdd.rightOuterJoin(other)` | Right outer join |
| `rdd.fullOuterJoin(other)` | Full outer join |
| `rdd.cogroup(other)` | Co-group by key |
| `rdd.combineByKey(createCombiner, mergeValue, mergeCombiners)` | General aggregation by key |
| `rdd.aggregateByKey(zeroValue, seqFunc, combFunc)` | Aggregate by key |
| `rdd.foldByKey(zeroValue, func)` | Fold by key |
| `rdd.countByKey()` | Count by key |
| `rdd.subtractByKey(other)` | Remove keys present in other |

### RDD Actions
| Method | Description |
|---|---|
| `rdd.collect()` | Return all elements |
| `rdd.count()` | Count elements |
| `rdd.first()` | First element |
| `rdd.take(n)` | First n elements |
| `rdd.takeOrdered(n, key=None)` | Smallest n elements |
| `rdd.top(n)` | Largest n elements |
| `rdd.takeSample(withReplacement, num, seed)` | Random sample |
| `rdd.reduce(f)` | Reduce all elements |
| `rdd.fold(zeroValue, f)` | Fold with initial value |
| `rdd.aggregate(zeroValue, seqOp, combOp)` | Aggregate |
| `rdd.foreach(f)` | Apply function to each element |
| `rdd.foreachPartition(f)` | Apply function to each partition |
| `rdd.countByValue()` | Count by value |
| `rdd.saveAsTextFile(path)` | Save as text file |
| `rdd.saveAsPickleFile(path)` | Save as pickle file |
| `rdd.getNumPartitions()` | Get number of partitions |
| `rdd.glom().collect()` | Visualize partitions |
| `rdd.toLocalIterator()` | Iterate locally |
| `rdd.isEmpty()` | Check if empty |
| `rdd.min()` | Minimum |
| `rdd.max()` | Maximum |
| `rdd.sum()` | Sum |
| `rdd.mean()` | Mean |
| `rdd.stdev()` | Standard deviation |
| `rdd.variance()` | Variance |
| `rdd.histogram(buckets)` | Histogram |
| `rdd.stats()` | StatCounter (count, mean, stdev, max, min) |

---

## Spark Streaming (Structured)

### Reading Streams
```python
# File source
df = spark.readStream \
    .format("csv") \
    .option("header", True) \
    .schema(schema) \
    .load("path/to/dir")

# Kafka source
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "host:9092") \
    .option("subscribe", "topic1") \
    .option("startingOffsets", "earliest") \
    .load()

# Socket source (testing)
df = spark.readStream \
    .format("socket") \
    .option("host", "localhost") \
    .option("port", 9999) \
    .load()

# Rate source (testing)
df = spark.readStream \
    .format("rate") \
    .option("rowsPerSecond", 10) \
    .load()
```

### Writing Streams
```python
query = df.writeStream \
    .outputMode("append") \         # append, complete, update
    .format("console") \            # console, parquet, kafka, memory, etc.
    .option("truncate", False) \
    .option("checkpointLocation", "path/to/checkpoint") \
    .trigger(processingTime="10 seconds") \  # or once=True, continuous="1 second"
    .start()

# To Kafka
query = df.writeStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "host:9092") \
    .option("topic", "output_topic") \
    .option("checkpointLocation", "path") \
    .start()

# Manage query
query.awaitTermination()
query.stop()
query.status
query.lastProgress
query.isActive
query.id
query.name
query.recentProgress
query.explain()
```

### Output Modes
| Mode | Description |
|---|---|
| `"append"` | Only new rows (no aggregation updates) |
| `"complete"` | Entire result table each trigger |
| `"update"` | Only changed rows |

### Trigger Types
```python
.trigger(processingTime="10 seconds")    # Micro-batch every 10s
.trigger(once=True)                       # Single micro-batch then stop
.trigger(availableNow=True)               # Process all available then stop
.trigger(continuous="1 second")           # Continuous processing (experimental)
```

### Streaming Query Manager
```python
spark.streams.active              # List of active queries
spark.streams.get(id)             # Get query by ID
spark.streams.awaitAnyTermination() # Wait for any query to terminate
spark.streams.resetTerminated()   # Reset terminated queries
```

---

## Configuration & Performance

### Common Spark Configurations
```python
# Memory
.config("spark.driver.memory", "4g")
.config("spark.executor.memory", "8g")
.config("spark.memory.fraction", "0.6")
.config("spark.memory.storageFraction", "0.5")

# Parallelism
.config("spark.default.parallelism", "200")
.config("spark.sql.shuffle.partitions", "200")

# Serialization
.config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")

# SQL
.config("spark.sql.adaptive.enabled", "true")           # Adaptive query execution
.config("spark.sql.adaptive.coalescePartitions.enabled", "true")
.config("spark.sql.autoBroadcastJoinThreshold", "10m")  # Auto broadcast threshold
.config("spark.sql.broadcastTimeout", "300")

# Dynamic allocation
.config("spark.dynamicAllocation.enabled", "true")
.config("spark.dynamicAllocation.minExecutors", "1")
.config("spark.dynamicAllocation.maxExecutors", "10")

# Network & I/O
.config("spark.network.timeout", "600s")
.config("spark.sql.files.maxPartitionBytes", "128m")
.config("spark.sql.files.openCostInBytes", "4m")

# Hive
.config("spark.sql.warehouse.dir", "/path/to/warehouse")
.config("hive.metastore.uris", "thrift://host:9083")
```

### DataFrame Performance Methods
| Method | Description |
|---|---|
| `df.explain(mode="simple")` | Show execution plan (simple/extended/codegen/cost/formatted) |
| `df.cache()` | Cache DataFrame |
| `df.persist(storageLevel)` | Persist with level |
| `df.unpersist()` | Remove from cache |
| `df.repartition(n)` | Repartition (shuffle) |
| `df.coalesce(n)` | Reduce partitions |
| `df.hint("broadcast")` | Optimizer hint |
| `df.checkpoint()` | Break lineage |

### Execution Plan
```python
df.explain()              # Simple physical plan
df.explain(True)          # Parsed, Analyzed, Optimized, Physical plans
df.explain("formatted")   # Formatted plan
df.explain("cost")        # With cost estimates
df.explain("codegen")     # With generated code
```

### Broadcast Variables & Accumulators
```python
# Broadcast variable (read-only shared variable)
broadcast_var = spark.sparkContext.broadcast([1, 2, 3])
broadcast_var.value  # Access the value
broadcast_var.unpersist()

# Accumulator (write-only shared variable)
counter = spark.sparkContext.accumulator(0)
rdd.foreach(lambda x: counter.add(1))
print(counter.value)
```

---

## JSON & Complex Type Functions

```python
from pyspark.sql.functions import (
    from_json, to_json, schema_of_json,
    get_json_object, json_tuple,
    to_csv, from_csv, schema_of_csv
)
```

| Function | Description |
|---|---|
| `from_json(col, schema)` | Parse JSON string to struct |
| `to_json(col)` | Convert struct/map/array to JSON string |
| `schema_of_json(json_str)` | Infer schema from JSON string |
| `get_json_object(col, path)` | Extract from JSON using path (e.g., `$.name`) |
| `json_tuple(col, *fields)` | Extract multiple fields from JSON |
| `from_csv(col, schema)` | Parse CSV string |
| `to_csv(col)` | Convert struct to CSV string |

```python
json_schema = schema_of_json('{"name": "Alice", "age": 25}')
df.withColumn("parsed", from_json(col("json_str"), json_schema))
df.withColumn("name", get_json_object(col("json_str"), "$.name"))
df.select(json_tuple(col("json_str"), "name", "age").alias("name", "age"))
df.withColumn("json", to_json(struct(col("name"), col("age"))))
```

---

## Miscellaneous

### DataFrame Properties
| Property | Description |
|---|---|
| `df.columns` | List of column names |
| `df.dtypes` | List of (name, type) tuples |
| `df.schema` | StructType schema |
| `df.rdd` | Underlying RDD |
| `df.isStreaming` | Whether this is a streaming DataFrame |
| `df.is_cached` | Whether cached |
| `df.storageLevel` | Storage level |
| `df.inputFiles()` | List of input files |

### DataFrame Statistical Methods
```python
df.stat.corr("col1", "col2")                  # Pearson correlation
df.stat.cov("col1", "col2")                   # Covariance
df.stat.crosstab("col1", "col2")              # Crosstab
df.stat.freqItems(["col1", "col2"], support=0.01)  # Frequent items
df.stat.approxQuantile("col", [0.25, 0.5, 0.75], relativeError=0.01)
df.stat.sampleBy("label", {0: 0.1, 1: 0.2})  # Stratified sample
```

### Useful Patterns
```python
# Chain multiple transformations
result = (df
    .filter(col("age") > 18)
    .withColumn("full_name", concat_ws(" ", col("first"), col("last")))
    .groupBy("department")
    .agg(avg("salary").alias("avg_salary"))
    .orderBy(col("avg_salary").desc())
)

# Multiple aggregations
from pyspark.sql.functions import count, avg, max, min, sum
result = df.groupBy("department").agg(
    count("*").alias("count"),
    avg("salary").alias("avg_salary"),
    max("salary").alias("max_salary"),
    min("salary").alias("min_salary"),
    sum("salary").alias("total_salary")
)

# Pivot table
pivot = df.groupBy("department").pivot("year").agg(sum("revenue"))

# Running SQL directly
df.createOrReplaceTempView("employees")
result = spark.sql("""
    SELECT department, 
           AVG(salary) as avg_salary,
           COUNT(*) as num_employees
    FROM employees 
    WHERE age > 25
    GROUP BY department
    HAVING COUNT(*) > 5
    ORDER BY avg_salary DESC
""")
```
