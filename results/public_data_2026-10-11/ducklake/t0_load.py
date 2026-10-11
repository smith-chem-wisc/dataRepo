import duckdb
con = duckdb.connect()
print("duckdb", duckdb.__version__)
con.execute("INSTALL ducklake; LOAD ducklake;")
print(con.execute("SELECT extension_name, loaded, installed, extension_version, install_mode, installed_from, install_path FROM duckdb_extensions() WHERE extension_name IN ('ducklake','parquet','httpfs')").fetchall())
print(con.execute("SELECT function_name FROM duckdb_functions() WHERE function_name LIKE 'ducklake%' GROUP BY 1 ORDER BY 1").fetchall())
print(con.execute("SELECT name, value, description FROM duckdb_settings() WHERE name ILIKE '%ducklake%'").fetchall())
