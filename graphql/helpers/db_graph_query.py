import psycopg2
import json
from django.db import connection


class GraphQL():

    def update_table(self, update_data):
        """
        Update data dynamically in a PostgreSQL table based on provided JSON data.
        
        Parameters:
        - connection_params (dict): Dictionary containing PostgreSQL connection parameters.
                                Should include keys: host, port, database, user, password.
        - update_data (dict): JSON data containing table name, set values, and condition for update.
                            Should have keys: table_name, set_values, condition.
                            Example: {
                                "table_name": "my_table",
                                "set_values": {"column1": "new_value1", "column2": "new_value2", ...},
                                "condition": "column_id = %s"
                            }
                            'condition' is a string representing the WHERE clause condition.
                            
        Returns:
        - int: Number of rows affected by the update.
        """
        rows_affected = 0
        
        try:
            # Establish connection to PostgreSQL
            
            conn = connection
            cur = conn.cursor()
            
            # Construct the SQL query dynamically
            set_values = ', '.join([f"{key} = %s" for key in update_data['set_values']])
            update_query = f"UPDATE {update_data['table_name']} SET {set_values} WHERE {update_data['condition']}"
            
            # Execute the update operation
            cur.execute(update_query, list(update_data['set_values'].values()))
            
            # Get the number of rows affected
            rows_affected = cur.rowcount
            
            # Commit the transaction
            conn.commit()
            print(f"Update successful. {rows_affected} rows affected.")
            
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error updating data: {error}")
            rows_affected = 0  # Reset rows_affected if there's an error
        
        finally:
            # Close communication with the database
            if conn is not None:
                conn.close()
        
        return rows_affected

    # Example usage:
    # if __name__ == "__main__update":
    #     # Example JSON data
    #     json_data = {
    #         "table_name": "my_table",
    #         "set_values": {"column1": "new_value1", "column2": "new_value2"},
    #         "condition": "id = %s"
    #     }
        
    #     # Example PostgreSQL connection parameters
    #     connection_params = {
    #         "host": "your_host",
    #         "port": "your_port",
    #         "database": "your_database",
    #         "user": "your_user",
    #         "password": "your_password"
    #     }
        
    #     # Call the function
    #     rows_affected = update_table(json_data)
        
    #     # Print the number of rows affected
    #     print("Rows affected:", rows_affected)


    def insert_into_table(self, insert_data):
        """
        Insert data dynamically into a PostgreSQL table based on provided JSON data.
        
        Parameters:
        - connection_params (dict): Dictionary containing PostgreSQL connection parameters.
                                Should include keys: host, port, database, user, password.
        - insert_data (dict): JSON data containing table name, columns, and values to insert.
                            Should have keys: table_name, columns, values.
                            Example: {
                                "table_name": "my_table",
                                "columns": ["column1", "column2", ...],
                                "values": [["value1", "value2", ...], ["value1", "value2", ...], ...]
                            }
        """
        try:
            # Establish connection to PostgreSQL
            conn = connection
            cur = conn.cursor()
            
            # Construct the SQL query dynamically
            columns = ', '.join(insert_data['columns'])
            values_template = ', '.join(['%s'] * len(insert_data['values'][0]))
            insert_query = f"INSERT INTO {insert_data['table_name']} ({columns}) VALUES ({values_template}) RETURNING id"
            
            # Execute the insertion for each set of values
            ids = []
            for values in insert_data['values']:
                cur.execute(insert_query, values)
                returned_id = cur.fetchone()[0] 
                ids.append(returned_id)
            
            # Commit the transaction
            conn.commit()
            print(ids)
            print("Insertion successful.") 
            
        except (Exception, psycopg2.DatabaseError) as error:
            ids.append(f"Error inserting data: {error}")
            print(f"Error inserting data: {error}")
        
        finally:
            # Close communication with the database
            if conn is not None:
                conn.close()
        return ids

    # Example usage:
    # if __name__ == "__main__insert":
    #     # Example JSON data
    #     json_data = {
    #         "table_name": "my_table",
    #         "columns": ["column1", "column2", "column3"],
    #         "values": [
    #             ["value1_row1", "value2_row1", "value3_row1"],
    #             ["value1_row2", "value2_row2", "value3_row2"]
    #         ]
    #     }
        
    #     # Example PostgreSQL connection parameters
    #     connection_params = {
    #         "host": "your_host",
    #         "port": "your_port",
    #         "database": "your_database",
    #         "user": "your_user",
    #         "password": "your_password"
    #     }
        
    #     # Call the function
    #     insert_into_table(json_data)



    def select_from_table(self, select_data):
        """
        Select data dynamically from a PostgreSQL table based on provided JSON data and return results in JSON format.
        
        Parameters:
        - connection_params (dict): Dictionary containing PostgreSQL connection parameters.
                                Should include keys: host, port, database, user, password.
        - select_data (dict): JSON data containing table name, columns, condition, and optional parameters for selection.
                            Should have keys: table_name, columns, condition, params (optional).
                            Example: {
                                "table_name": "my_table",
                                "columns": ["column1", "column2", ...],
                                "condition": "column1 = %s",
                                "params": ["value1"]
                            }
                            'condition' is a string representing the WHERE clause condition.
                            'params' is a list of parameters for the condition placeholders.
                            
        Returns:
        - str: JSON string representing selected rows from the table.
        """
        selected_rows = []
        page_size = select_data.get('page_size', 10)
        page_number = select_data.get('page_number', 1)
        offset = (page_number - 1) * page_size
        
        try:
            # Establish connection to PostgreSQL
            conn = connection
            cur = conn.cursor()

            total_rows = None
            total_pages = None

            if 'page_size' in select_data and 'page_number' in select_data:
                # Construct the count query to get the total number of rows
                count_query = f"SELECT COUNT(*) FROM {select_data['table_name']}"
                if 'condition' in select_data:
                    count_query += f" WHERE {select_data['condition']}"

                # Execute the count query
                if 'params' in select_data:
                    cur.execute(count_query, select_data['params'])
                else:
                    cur.execute(count_query)

                # Fetch the total number of rows
                total_rows = cur.fetchone()[0]
                total_pages = (total_rows + page_size - 1) // page_size  # Calculate total pages
            
            # Construct the SQL query dynamically
            columns = ', '.join(select_data['columns']) if 'columns' in select_data else '*'
            select_query = f"SELECT {columns} FROM {select_data['table_name']}"
            if 'condition' in select_data:
                select_query += f" WHERE {select_data['condition']}"

            if 'page_size' in select_data and 'page_number' in select_data:
                select_query += f" LIMIT {page_size} OFFSET {offset}"

            # Execute the select operation
            if 'params' in select_data:
                cur.execute(select_query, select_data['params'])
            else:
                cur.execute(select_query)
            
            # Fetch all selected rows
            selected_rows = cur.fetchall()
            
            # Convert selected rows to JSON format
            columns = [desc[0] for desc in cur.description]  # Get column names
            results = []
            for row in selected_rows:
                results.append(dict(zip(columns, row)))
            
            json_output = json.dumps(results, default=str)  # Convert to JSON string
            
            print(f"Selection successful. {len(selected_rows)} rows selected.")
            
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error selecting data: {error}")
            json_output = "[]"  # Return empty JSON array if there's an error
        
        finally:
            # Close communication with the database
            if conn is not None:
                conn.close()
        
        # return json_output
        return results, total_rows, total_pages

    # Example usage:
    # if __name__ == "__main__select":
    #     # Example JSON data
    #     json_data = {
    #         "table_name": "my_table",
    #         "columns": ["column1", "column2", "column3"],
    #         "condition": "column1 = %s",
    #         "params": ["value1"]
    #     }
        
    #     # Example PostgreSQL connection parameters
    #     connection_params = {
    #         "host": "your_host",
    #         "port": "your_port",
    #         "database": "your_database",
    #         "user": "your_user",
    #         "password": "your_password"
    #     }
        
    #     # Call the function
    #     json_results = select_from_table(json_data)
        
    #     # Print the JSON results
    #     print("Selected rows (JSON format):")
    #     print(json_results)


    def delete_from_table(self, delete_data):
        """
        Delete data dynamically from a PostgreSQL table based on provided JSON data.
        
        Parameters:
        - connection_params (dict): Dictionary containing PostgreSQL connection parameters.
                                Should include keys: host, port, database, user, password.
        - delete_data (dict): JSON data containing table name and condition for deletion.
                            Should have keys: table_name, condition, params (optional).
                            Example: {
                                "table_name": "my_table",
                                "condition": "column1 = %s",
                                "params": ["value1"]
                            }
                            'condition' is a string representing the WHERE clause condition.
                            'params' is a list of parameters for the condition placeholders.
                            
        Returns:
        - int: Number of rows affected by the deletion.
        """
        rows_deleted = 0
        
        try:
            # Establish connection to PostgreSQL
            conn = connection
            cur = conn.cursor()
            
            # Construct the SQL query dynamically
            delete_query = f"DELETE FROM {delete_data['table_name']} WHERE {delete_data['condition']}"
            
            # Execute the delete operation
            if 'params' in delete_data:
                cur.execute(delete_query, delete_data['params'])
            else:
                cur.execute(delete_query)
            
            # Get the number of rows affected
            rows_deleted = cur.rowcount
            
            # Commit the transaction
            conn.commit()
            print(f"Deletion successful. {rows_deleted} rows deleted.")
            
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error deleting data: {error}")
            rows_deleted = 0  # Reset rows_deleted if there's an error
        
        finally:
            # Close communication with the database
            if conn is not None:
                conn.close()
        
        return rows_deleted

    # Example usage:
    # if __name__ == "__main__delete":
    #     # Example JSON data
    #     json_data = {
    #         "table_name": "my_table",
    #         "condition": "column1 = %s",
    #         "params": ["value1"]
    #     }
        
    #     # Example PostgreSQL connection parameters
    #     connection_params = {
    #         "host": "your_host",
    #         "port": "your_port",
    #         "database": "your_database",
    #         "user": "your_user",
    #         "password": "your_password"
    #     }
        
    #     # Call the function
    #     rows_deleted = delete_from_table(json_data)
        
    #     # Print the number of rows deleted
    #     print("Rows deleted:", rows_deleted)