"""
MySQL : utiliser mysqlclient si installé ; sinon PyMySQL en remplacement de MySQLdb.
"""

try:
    import MySQLdb  # noqa: F401 — mysqlclient
except ImportError:
    import pymysql

    pymysql.install_as_MySQLdb()
