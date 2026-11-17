# ai-generated: 100% - GitHub Copilot wrote Semgrep rule tests for broad exception handling and SQL interpolation


def catches_anything():
    try:
        perform_request()
    # ruleid: svcdesk-no-catch-all-exception
    except Exception:
        return None


def catches_expected_error():
    try:
        perform_request()
    # ok: svcdesk-no-catch-all-exception
    except TimeoutError:
        return None


def builds_sql_from_input(connection, user_value):
    # ruleid: svcdesk-no-sql-fstring
    connection.execute(f"SELECT * FROM tickets WHERE title = '{user_value}'")


def binds_sql_value(connection, user_value):
    # ok: svcdesk-no-sql-fstring
    connection.execute("SELECT * FROM tickets WHERE title = ?", (user_value,))