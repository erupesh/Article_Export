class DbOperation:
    
    """
    Class for performing database operations.

    Attributes:
    - dsn (str): The DSN used to connect to the database.
    - logger (object): The logger object for logging.
    - cursor: The cursor object for interacting with the database.
    - columns_list (dict): A dictionary mapping table names to column lists.

    Methods:
    - __init__(self, dsn: str, logHangle=None): Constructor method.
    - search_table(self, tableName: str, condition: str='', sortBy: str=''): Method to search records in a table.
    - update_field(self, tableName: str, column: str, value: int, condColumn: str, condValue: str): Method to update a field in a table.
    - update_record(self, tableName: str, column_value_dict: dict, condColumn: str, condValue: str): Method to update a record in a table.
    """

    def __init__(self: object, dsn: str, logHangle=None) -> None:

        """
        Initialize DbOperation with a DSN and an optional logger object.

        Args:
        - dsn (str): The DSN used to connect to the database.
        - logHangle (object, optional): The logger object for logging. Defaults to None.
        """

        self.logger = logHangle
        self.dsn = dsn
        self.cursor = None
        self.logger = None

        self.columns_list ={
        'Articles': [],
        'autoabstract': []
        }
        pass 

    def search_table(self: object, tableName: str, condition: str='', sortBy: str=''):

        """
        Search records in a table.

        Args:
        - tableName (str): The name of the table to search in.
        - condition (str, optional): The condition for the search. Defaults to ''.
        - sortBy (str, optional): The column to sort by. Defaults to ''.

        Returns:
        - list: A list of records matching the search criteria.
        """

        import pyodbc

        if tableName == '':
            return

        queryString = "SELECT * FROM " + tableName

        if condition != '':
            queryString += " WHERE " + condition

        if sortBy != '':
            queryString += " ORDER BY " + sortBy
        
        connString = "DSN=" + self.dsn
        conn = pyodbc.connect(connString)
        self.cursor = conn.cursor()

        if self.logger:
            self.logger.info(queryString)
        self.cursor.execute(queryString)
        
        result = self.cursor.fetchall() #due to old CHAR type data if any
        
        i = -1
        for row in result:
            i +=1
            for j in range(len(row)):
                if type(result[i][j]) == str:
                    result[i][j] = result[i][j].strip()
        
        return result


    def update_field(self: object, tableName: str, column: str, value: int, condColumn: str, condValue: str):


        """
        Update a field in a table.

        Args:
        - tableName (str): The name of the table to update.
        - column (str): The column to update.
        - value (int): The new value for the column.
        - condColumn (str): The column for the condition.
        - condValue (str): The value for the condition.

        Returns:
        - None
        """

        import pyodbc
        
        # return

        connString = "DSN=" + self.dsn
        connection = pyodbc.connect(connString)

        # Create a cursor object to interact with the database
        self.cursor = connection.cursor()

        if type(condValue)==str:
            condValue = "'" + condValue + "'"
        if type(value)==str:
            value = "'" + value + "'"

        # update_query = "UPDATE your_table SET column1 = ?, column2 = ? WHERE condition_column = ?"
        update_query = "UPDATE " + tableName + " SET " + column +" =" + str(value) + " where " + condColumn + ' =' + str(condValue)

        if self.logger:
            self.logger.info(update_query)
        # Execute the update query with parameters
        self.cursor.execute(update_query)

        # Commit the changes to the database
        connection.commit()


    def update_record(self: object, tableName: str, column_value_dict: dict, condColumn: str, condValue: str):

        """
        Update a record in a table.

        Args:
        - tableName (str): The name of the table to update.
        - column_value_dict (dict): A dictionary mapping column names to new values.
        - condColumn (str): The column for the condition.
        - condValue (str): The value for the condition.

        Returns:
        - None
        """

        import pyodbc
        
        # return

        connString = "DSN=" + self.dsn
        connection = pyodbc.connect(connString)

        # Create a cursor object to interact with the database
        self.cursor = connection.cursor()
        
        if type(condValue)==str:
            condValue = "'" + condValue + "'"
        
        str_column_value = ""
        for column, value in column_value_dict.items():
            if type(value)==str:
                value = "'" + value + "'"
            if str_column_value != "":
                str_column_value += "," #comma separator for multiple columns
            str_column_value += column +" =" + str(value)

        # update_query = "UPDATE your_table SET column1 = ?, column2 = ? WHERE condition_column = ?"
        update_query = "UPDATE " + tableName + " SET " + str_column_value + " where " + condColumn + ' =' + str(condValue)

        if self.logger:
            self.logger.info(update_query)
        # Execute the update query with parameters
        self.cursor.execute(update_query)

        # Commit the changes to the database
        connection.commit()
